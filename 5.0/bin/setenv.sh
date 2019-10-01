#!/bin/sh

  #JAVA_HOME="/usr/lib/jvm/jre"
  #export JAVA_HOME

export UMASK='0022'

CATALINA_BASE="/usr/local/tomcat"
export CATALINA_BASE

CONTENT_ROOT="-Dtds.content.root.path=/usr/local/tds/content/"
NORMAL="-Xmx4g -Xms512m -server"
HEADLESS="-Djava.awt.headless=true"
JAVA_PREFS="-Djava.util.prefs.systemRoot=$CONTENT_ROOT/thredds/javaUtilPrefs -Djava.util.prefs.userRoot=$CONTENT_ROOT/thredds/javaUtilPrefs"

JAVA_OPTS="-Djava.net.preferIPv4Stack=true -Djava.net.preferIPv4Addresses=true"
export JAVA_OPTS

CATALINA_OPTS="$NORMAL $CONTENT_ROOT $HEADLESS $JAVA_PREFS $JAVA_OPTS"
export CATALINA_OPTS
