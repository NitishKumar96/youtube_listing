FROM python:latest
# make the folder and go inside it
RUN mkdir /home/www-data
# in dockerfile use workdir cd donot work
WORKDIR /home/www-data
# download web2py and unzip it
RUN wget http://web2py.com/examples/static/web2py_src.zip
RUN unzip web2py_src.zip
RUN cp web2py/handlers/wsgihandler.py web2py
RUN chown -R www-data:www-data web2py

# add this line to get into web2py folder and rusn the command
WORKDIR /
WORKDIR home/www-data/web2py
COPY web2py.crt /home/www-data/web2py
COPY web2py.key /home/www-data/web2py
RUN python -c "from gluon.main import save_password; save_password('admin_password:1', 443)"

EXPOSE 8000
EXPOSE 8080
# ##### INSTALL ALL LIBS AND DEPENDENCIES
#  to connect to postgres db
RUN pip install psycopg2
# #####

#  final run command
CMD python web2py.py --no_gui -c web2py.crt -k web2py.key -a admin -i 0.0.0.0 -p 80

