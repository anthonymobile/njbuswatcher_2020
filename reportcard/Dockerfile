# base python supervisor image
FROM praekeltfoundation/supervisor

WORKDIR /home
COPY requirements.txt /home
RUN pip install --no-cache-dir -r requirements.txt

# copy the supervisor conf file
ADD ./reportcard/supervisord/reportcard.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .
