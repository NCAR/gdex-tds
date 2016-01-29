/**
 * 
 */
package edu.ucar.rda.RDARealms;

import java.security.Principal;
import java.sql.SQLException;
import java.sql.Connection;
import java.util.ArrayList;

import org.apache.catalina.realm.GenericPrincipal;
import org.apache.catalina.realm.JDBCRealm;
import org.apache.juli.logging.Log;
import org.apache.juli.logging.LogFactory;

//import com.mysql.jdbc.Connection;

/**
 * FIXME: Requires tomcat-juli.jar file found in $TOMCAT_HOME/bin
 */

/**
 * @author manross
 *
 */
public class RDA_JDBCRealm extends JDBCRealm {
	private static Log log = LogFactory.getLog(RDA_JDBCRealm.class);

    /**
     * Return the Principal associated with the specified username and
     * credentials, if there is one; otherwise return <code>null</code>.
     *
     * If there are any errors with the JDBC connection, executing
     * the query or anything we return null (don't authenticate). This
     * event is also logged, and the connection will be closed so that
     * a subsequent request will automatically re-open it.
     *
     * @param username Username of the Principal to look up
     * @param credentials Password or other credentials to use in
     *  authenticating this username
     *  
     *  @override seems as if this method is also needed in this extended 
     *  class to make sure the following method gets called. 
     */
    public Principal authenticate(String username, String credentials) {

    	
    	
//    	log.info( "First: " +
//				"U: " + username +
//				"P: " + credentials);
    	
       // No user or no credentials
        // Can't possibly authenticate, don't bother the database then
       if (username == null || credentials == null) {
               return null;
       }

       Connection dbConnection = null;

        try {

            // Ensure that we have an open database connection
            dbConnection = open();
            if (dbConnection == null) {
                // If the db connection open fails, return "not authenticated"
                return null;
            }

            // Acquire a Principal object for this user
            return authenticate(dbConnection, username, credentials);

        } catch (SQLException e) {
            // Log the problem for posterity
            containerLog.error(sm.getString("dataSourceRealm.exception"), e);

            // Return "not authenticated" for this request
            return (null);

        } finally {
               close(dbConnection);
        }

    }

	
	/**
	 * Return the Principal associated with the specified username and
	 * credentials, if there is one; otherwise return <code>null</code>.
	 *
	 * @param dbConnection The database connection to be used
	 * @param username Username of the Principal to look up
	 * @param credentials Password or other credentials to use in
	 *  authenticating this username
	 * 
	 * @override to incorporate Unix Crypt instead of default digest options 
	 * @author manross
	 * 
	 * 
	 */
	public synchronized Principal authenticate(Connection dbConnection,
            String username,
            String credentials) {

		
//		log.info( "Second: " +
 //					"U: " + username +
//					"P: " + credentials);
		
		// No user or no credentials
		// Can't possibly authenticate, don't bother the database then
		if (username == null || credentials == null) {
			return null;
		}
		
		if (username.contains("%40")) {
//			log.info("Replacing username...");
			username = username.replace("%40", "@");
		}
		
		
//		log.info( "222 Second 222: " +
//				"U: " + username +
//				"P: " + credentials);
		
		
		// Look up the user's credentials
		String dbCredentials = getPassword(username);
		
		// Get NullString error if we fail to get password
		if (dbCredentials == null){
			return null;
		}
		
  		//log.info( "Credentials! " + dbCredentials);
		
		// User's credentials stored via Unix Crypt with first two characters being a random "salt"
		// We need to grab the first two characters to use as the salt for the crypt method to compare
		// passwords
		String salt = dbCredentials.substring(0,2);
		
		// Validate the user's credentials
		boolean validated = false;
		if (hasMessageDigest()) {
			// This is where we incorporate Unix Crypt to match Bob's C implementation
			validated = (UnixCrypt.crypt(salt, (credentials)).equalsIgnoreCase(dbCredentials));
		} else {
			// This is where we incorporate Unix Crypt to match Bob's C implementation
			validated = (UnixCrypt.crypt(salt, (credentials)).equals(dbCredentials));
		}
		
		if (validated) {
			if (log.isTraceEnabled())
			log.trace(sm.getString("jdbcRealm.authenticateSuccess",
			             username));
		} else {
			if (log.isTraceEnabled())
			log.trace(sm.getString("jdbcRealm.authenticateFailure",
			             username));
			return (null);
		}
	
                ArrayList<String> roles = getRoles(username);	
               roles.add("odap");		
		/** 
		 * Need to define a role to match with web.xml <auth-constraint><role-name>
		 * Hardwiring odap for now. 
		 * 
		 * TODO: possibly add role to ruser_access table acode column?
		 */
//		 ArrayList<String> roles = new ArrayList<String>() {{ add("odap"); }};
		
//			log.info(
//					"U: " + username +
//					"\nP: " + credentials +
//					"\nS: " + salt +
//					"\nC: " + UnixCrypt.crypt(salt, (credentials)) +
//					"\nD: " + dbCredentials +
//					"\nV: " + validated +
//					"\nG: " + new GenericPrincipal(username, credentials, roles)
//					);
		
		// Create and return a suitable Principal for this user
		return (new GenericPrincipal(username, credentials, roles));
		
	}
	
	/**
	 * 
	 */
	public RDA_JDBCRealm() {
		// TODO Auto-generated constructor stub
	}

//	/**
//	 * @param args
//	 */
//	public static void main(String[] args) {
//		// TODO Auto-generated method stub
//
//	}

}
