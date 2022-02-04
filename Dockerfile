FROM continuumio/miniconda3

LABEL MAINTAINER="Doaa Altarawy <doaa.altarawy@gmail.com>, Levi Naden <lnaden@vt.edu>"


ENV GROUP_ID=1000 \
    USER_ID=1000

WORKDIR /var/www/

ADD ./requirements.txt /var/www/requirements.txt

# Copy over the run scripts
COPY ./app/qp/QikProp /QikProp
# Setup QikProp Environment variable
ENV QPdir /QikProp

# what's only needed for continuumio/miniconda3
RUN apt-get --allow-releaseinfo-change update && \
    pip install --upgrade pip && \
    apt-get install -y --no-install-recommends npm && \
    # QikProp thigs for the ELF 32-bit LSB executable that it is
    # Adding this here because I suspect its dangerous before previous
    dpkg --add-architecture i386 && \
    apt-get update  && \
    apt-get install -y libgcc1:i386 tcsh && \
    rm -rf /var/lib/apt/lists/*  && \
    mkdir /qprun && \
    # Cleanup from apt now that we're done with it
    rm -rf /var/lib/apt/lists/*  && \
    # Python
    pip install --no-cache-dir -r requirements.txt && \
    conda clean -y --all


ADD . /var/www/

# Install Javascript requirements (from package.json file)
RUN cd app/static && \
    npm install && \
    rm -rf /var/lib/apt/lists/*

# Make the I/O directories for workers pre-mount (else it mounts as root)
# Make the user who will be doing the ops
# own everything in the dir by the user
RUN mkdir /var/www/qpin /var/www/qpout && \
    groupadd -g $GROUP_ID www  && \
    useradd -r -g www -s /bin/sh -u $USER_ID www  && \
    chown -R www:www /var/www

# Become the user
USER www


# Listens on port, doesn't publish it. Publish by -p or ports in docker-compose
EXPOSE 5001

# Run in Exec form, can't be overriden
ENTRYPOINT [ "gunicorn", "--bind", "0.0.0.0:5001", "--timeout", "300", "covid_apis:app"]
# Params to pass to ENTRYPOINT, and can be overriden when running containers
CMD ["-w", "2", "--access-logfile", "/var/www/logs/access.log", "--error-logfile", "/var/www/logs/error.log"]

# can't override ENTRYPOINT shell form
#ENTRYPOINT gunicorn --bind :5000 --access-logfile - --error-logfile - qcarchive_web:app

