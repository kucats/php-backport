FROM quay.io/centos/centos@sha256:e4ca2ed0202e76be184e75fb26d14bf974193579039d5573fb2348664deef76e
RUN rm -f /etc/yum.repos.d/*.repo
COPY CentOS-Vault.repo /etc/yum.repos.d/CentOS-Vault.repo
RUN yum -y install yum-utils rpm-build redhat-rpm-config gcc gcc-c++ make \
    && yum clean all
COPY php-5.4.16-48.el7.src.rpm /tmp/php.src.rpm
RUN echo '84cfffd22e99e87e1f25f5e69f74108d762bab94759ef62079092382c89c06f1  /tmp/php.src.rpm' | sha256sum -c - \
    && rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 \
    && rpm -K /tmp/php.src.rpm \
    && yum-builddep -y /tmp/php.src.rpm \
    && yum -y install httpd curl python3 \
       php-5.4.16-48.el7 php-cli-5.4.16-48.el7 php-common-5.4.16-48.el7 \
       php-mbstring-5.4.16-48.el7 php-devel-5.4.16-48.el7 \
    && yum clean all
RUN useradd -m builder && mkdir -p /build/rpmbuild \
    && rpm -ivh --define '_topdir /build/rpmbuild' /tmp/php.src.rpm \
    && chown -R builder:builder /build
WORKDIR /build
