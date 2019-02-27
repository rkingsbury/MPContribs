FROM amancevice/pandas:0.23.4-python3-alpine
RUN apk add git make gcc musl-dev npm py3-pip libgfortran build-base \
    libstdc++ libpng libpng-dev freetype freetype-dev gfortran lapack-dev \
    libxml2-dev libxslt-dev py3-lxml

RUN pip3 install -U pip
RUN pip3 install -U setuptools
RUN pip3 install matplotlib
RUN pip3 install scipy

WORKDIR /app

COPY mpcontribs-portal/requirements.txt requirements-portal.txt
COPY mpcontribs-explorer/requirements.txt requirements-explorer.txt
COPY mpcontribs-users/requirements.txt requirements-users.txt
COPY mpcontribs-webtzite/requirements.txt requirements-webtzite.txt

RUN pip3 install -r requirements-portal.txt
RUN pip3 install -r requirements-explorer.txt
RUN pip3 install -r requirements-users.txt
RUN pip3 install -r requirements-webtzite.txt

#RUN apk add --no-cache build-base npm git linux-headers \
#      python2 py2-pip py2-numpy py2-scipy py2-psutil py2-libxml2 py2-lxml \
#      freetype-dev libpng-dev apache2-dev libffi-dev libxml2-dev bash vim
#RUN apk add --no-cache --allow-untrusted --repository \
#      http://dl-3.alpinelinux.org/alpine/edge/testing \
#      hdf5 hdf5-dev
#RUN pip install --no-cache-dir --no-binary :all: tables h5py

EXPOSE 8080
ENV PYTHONUNBUFFERED 1
ENV NODE_ENV production

WORKDIR /app

COPY mpcontribs-webtzite mpcontribs-webtzite
RUN cd mpcontribs-webtzite && pip install .

COPY mpcontribs-portal mpcontribs-portal
RUN cd mpcontribs-portal && pip install .

COPY package.json .
RUN npm install 2>&1

COPY mpcontribs-users mpcontribs-users
RUN cd mpcontribs-users && pip install .

COPY mpcontribs-explorer mpcontribs-explorer
RUN cd mpcontribs-explorer && pip install .

COPY test_site test_site

COPY webpack.config.js .
RUN npm run webpack 2>&1

COPY manage.py .
RUN python3 manage.py collectstatic --no-input && \
        python3 manage.py makemigrations webtzite && \
        python3 manage.py migrate && \
        python3 manage.py clearsessions && \
        python3 manage.py django_cas_ng_clean_sessions

CMD ["python3",  "manage.py", "runserver", "0.0.0.0:8080"]
