
## Steps to transition to a new version of thredds
Note: this may not work the same with every upgrade due to varying levels of change between versions


1. Shut down tomcat if already active
2. In $CATHOME/webapps remove previous version. So the .war file and directory it creates
3. cp new war file into $CATHOME/webapps
4. go to $CATHOME/conf/Catalina/localhost and change name match new warfile. Also, go into  the file and change reference to old name
5. start up tomcat 
6. cp web.xml into $CATHOME/webapps/thredds##version/WEB-INF/ which should be newly created
