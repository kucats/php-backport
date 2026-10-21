/* Test-only instrumentation. Never package or load on production. */
#include "php.h"
#include "SAPI.h"
#include "Zend/zend_globals.h"
#include "Zend/zend_alloc.h"

static unsigned long early_mask;
static zend_mm_mem_handlers original_handlers;
static zend_mm_mem_handlers failing_handlers;
static zend_mm_storage *injected_storage;

static PHP_INI_MH(ko_lab_check_early)
{
	unsigned long mask = 0;
	int i;
	if (EG(user_error_handler)) mask |= 1;
	if (EG(user_exception_handler)) mask |= 2;
	if (EG(exception) || EG(prev_exception)) mask |= 4;
	if (EG(error_handling) != EH_NORMAL) mask |= 8;
	if (EG(objects_store).object_buckets) mask |= 16;
	for (i = 0; i < sizeof(PG(http_globals)) / sizeof(PG(http_globals)[0]); i++) {
		if (PG(http_globals)[i]) mask |= 32;
	}
	if (PG(modules_activated)) mask |= 64;
	if (EG(user_error_handlers).elements || EG(user_exception_handlers).elements ||
		EG(user_error_handlers_error_reporting).elements) mask |= 128;
	if (SG(request_info).auth_user || SG(request_info).auth_password ||
		SG(request_info).auth_digest || SG(request_info).current_user ||
		SG(request_info).content_type_dup) mask |= 256;
	if (SG(sapi_headers).headers.head || SG(sapi_headers).headers.tail) mask |= 512;
	early_mask = mask;
	return SUCCESS;
}

PHP_INI_BEGIN()
	PHP_INI_ENTRY("ko_lab.early_check", "0", PHP_INI_PERDIR, ko_lab_check_early)
PHP_INI_END()

PHP_FUNCTION(ko_lab_early_state)
{
	RETURN_LONG(early_mask);
}

static zend_mm_segment *fail_storage_alloc(zend_mm_storage *storage, size_t size)
{
	(void)storage;
	(void)size;
	return NULL;
}

PHP_FUNCTION(ko_lab_underlying_oom)
{
	zend_mm_heap *heap;
	zend_mm_storage *storage;
	void *ptr;
	/* Obtain and immediately restore the current heap without allocating. */
	heap = zend_mm_set_heap(NULL TSRMLS_CC);
	zend_mm_set_heap(heap TSRMLS_CC);
	storage = zend_mm_get_storage(heap);
	original_handlers = *storage->handlers;
	failing_handlers = original_handlers;
	failing_handlers._alloc = fail_storage_alloc;
	storage->handlers = &failing_handlers;
	injected_storage = storage;
	zend_set_memory_limit((size_t)-1);
	ptr = emalloc(64 * 1024 * 1024);
	(void)ptr;
	RETURN_FALSE;
}

PHP_FUNCTION(ko_lab_size_overflow)
{
	void *ptr = safe_emalloc((size_t)-1, 16, 1);
	(void)ptr;
	RETURN_FALSE;
}

static PHP_MINIT_FUNCTION(ko_lab)
{
	REGISTER_INI_ENTRIES();
	return SUCCESS;
}

static PHP_MSHUTDOWN_FUNCTION(ko_lab)
{
	UNREGISTER_INI_ENTRIES();
	return SUCCESS;
}

static PHP_RSHUTDOWN_FUNCTION(ko_lab)
{
	/* End the synthetic fault when the unpatched engine uses normal shutdown. */
	if (injected_storage) {
		injected_storage->handlers = &original_handlers;
		injected_storage = NULL;
	}
	return SUCCESS;
}

static const zend_function_entry ko_lab_functions[] = {
	PHP_FE(ko_lab_early_state, NULL)
	PHP_FE(ko_lab_underlying_oom, NULL)
	PHP_FE(ko_lab_size_overflow, NULL)
	PHP_FE_END
};

zend_module_entry ko_lab_module_entry = {
	STANDARD_MODULE_HEADER,
	"ko_lab", ko_lab_functions,
	PHP_MINIT(ko_lab), PHP_MSHUTDOWN(ko_lab),
	NULL, PHP_RSHUTDOWN(ko_lab), NULL, "0.1", STANDARD_MODULE_PROPERTIES
};

ZEND_GET_MODULE(ko_lab)
