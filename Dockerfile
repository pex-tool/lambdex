# This is a minimum Amazon Linux environment that contains 'pex'
# It can be tailored to a certain extent in order to build Amazon Linux pex files.
#
# See http://docs.aws.amazon.com/AmazonECR/latest/userguide/amazon_linux_container_image.html
# for more info about the parent image.

FROM 137112412989.dkr.ecr.us-west-2.amazonaws.com/amazonlinux

RUN yum upgrade -y && yum install -y python27-pip.noarch
RUN pip install pex requests wheel
