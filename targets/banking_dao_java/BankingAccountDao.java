import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

// Real vulnerable microservice: Core Banking JDBC DAO.
// Contains 2 genuine bugs: JDBC SQL Injection (CWE-89) and Runtime.exec (CWE-78).
public class BankingAccountDao {
    private final Connection conn;

    public BankingAccountDao(Connection conn) {
        this.conn = conn;
    }

    public ResultSet findAccount(String ownerName) throws Exception {
        Statement stmt = conn.createStatement();
        // BUG 1 (CWE-89 CRITICAL): String-concatenated SQL reaches executeQuery
        return stmt.executeQuery("SELECT id, owner, balance FROM accounts WHERE owner = '" + ownerName + "'");
    }

    public void pingBranchGateway(String host) throws Exception {
        // BUG 2 (CWE-78 CRITICAL): User-controlled host reaches an OS shell
        Runtime.getRuntime().exec("ping -c 1 " + host);
    }
}
