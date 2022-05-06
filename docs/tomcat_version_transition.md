
## Steps to transition to a new version of tomcat
Note: this may not work the same with every upgrade due to varying levels of change between versions


1. Install new version. Typically will go in /usr/local
2. Change permisions on directory to tomcat
    2.1. As root. ```chown -R tomcat:tomcat directory```
3. Symlink content/ and logs/ directories
4. copy old bin/setenv.sh to new bin/
5. Copy thredds war file
6. shutdown any tomcat already active
7. Add conf/Catalina/localhost/thredds.xml
8. startup tomcat in new directory
9. change permissions on directories and files. By default, after warfile has been loaded, permissions are not correct
try
```catdo find . -type d | catdo xargs chmod 755 ``` And
```catdo find . -type f | catdo xargs chmod 644 ```
8. copy bin/setenv.sh 
9. replace .../tomcat/webapps/thredds##xxxx/WEB-INF/web.xml with one in repo
10. copy/soft link lib/ files



