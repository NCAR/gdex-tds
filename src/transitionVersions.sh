#!/bin/bash


usage()
{
    echo
    echo "Usage:"
    echo "$0 [Old tomcat directory] [New tomcat directory]"
    echo
    echo "Example:"
    echo "$0 /usr/local/apache-tomcat-8.0.36 /usr/local/apache-tomcat-8.5.43"
    exit 1
}
killTomcat()
{
    ps -ef | grep tomcat | grep -v grep | awk '{print $2}' | xargs kill
}
# Check args
if [[ -z $2 ]]; then
        usage
fi
echo "Need to switch to tomcat"
if [[ `whoami` != 'tomcat' ]]; then
    echo
    echo "Please execute this script as tomcat."
    echo "e.g. sudo -u tomcat $0"
    exit 1
fi


oldTomcat=$1
newTomcat=$2


# Symlink content and logs dirs.
cd $oldTomcat
contentDir=/data/tomcat/content
logsDir=/data/logs/tomcat

echo "Before you do anything, please execute this as root:"
echo "sudo -u root chown -R tomcat:tomcat $newTomcat; sudo -u root ln -s $contentDir content"

printf "Done? "
read a

# Symklink
rmdir logs
ln -s $logsDir logs

# Copy TDS warfile
cp $oldTomcat/webapps/thredds*war $newTomcat/webapps/

# Copy conf/localhost/*thredds*xml
localhostDir=conf/Catalina/localhost
mkdir -p $newTomcat/$localhostDir
cp $oldTomcat/$localhostDir/*.xml $newTomcat/$localhostDir/

# copy setenv.sh
cp $oldTomcat/bin/setenv.sh $newTomcat/bin/

# copy and link libs
ln -s /usr/share/java/apache-commons-collections.jar $newTomcat/lib/commons-collections.jar
ln -s /usr/share/java/apache-commons-dbcp.jar $newTomcat/lib/commons-dbcp.jar
ln -s /usr/share/java/apache-commons-pool.jar $newTomcat/lib/commons-pool.jar
ln -s /usr/share/java/ecj.jar $newTomcat/lib/jasper-jdt.jar
ln -s /usr/share/java/log4j.jar $newTomcat/lib/log4j.jar
ln -s /usr/local/tomcat/bin/tomcat-juli.jar $newTomcat/lib/tomcat-juli.jar
cp $oldTomcat/lib/mysql-connector-java-5.1.35-bin.jar $newTomcat/lib
cp $oldTomcat/lib/commons-codec-1.10.jar $newTomcat/lib

# Change permissions
find . -maxdepth 1 -type f | xargs chmod 644

# Startup
#killTomcat
sleep 5

#compile java
cp -r /gpfs/u/home/rpconroy/repositories/rda-tds/5.0/RDA_RealmSourceCode $newTomcat/work/
cd $newTomcat/work/RDA_RealmSourceCode/src/edu/ucar/rda/RDARealms
javac -cp $newTomcat/lib/catalina.jar:$newTomcat/lib/tomcat-juli.jar:$newTomcat/lib/tomcat-util.jar:$newTomcat/lib/commons-codec-1.10.jar *.java
cp *.class $newTomcat/work/RDA_RealmSourceCode/build/classes
cd $newTomcat/work/RDA_RealmSourceCode/build/classes
jar cf edu.ucar.rda.RDARealms.jar edu
cp edu.ucar.rda.RDARealms.jar $newTomcat/lib
cd $newTomcat


# startup tomcat
./bin/startup.sh
