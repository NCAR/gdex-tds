#java -Xmx32g -Dtds.content.root.path=/usr/local/tds/content -jar tdm-5.0.jar -nthreads 1 -tds "http://rda.ucar.edu:8080/" -cred tdm:tdsTrig

#java -Xmx32g -Dtds.content.root.path=/usr/local/tds/content -jar tdm-5.0.jar -nthreads 1 -tds "https://rda.ucar.edu:8443/" -cred tdm:tdsTrig

java -Xmx32g -Dtds.content.root.path=/usr/local/tds/content -jar tdmFat-5.0.0-beta5.jar -nthreads 1 -tds "https://rda.ucar.edu:8443/" -cred tdm:tdsTrig
