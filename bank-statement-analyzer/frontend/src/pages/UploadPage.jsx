import { useNavigate } from "react-router-dom";
import UploadStatement from "../components/UploadStatement.jsx";

export default function UploadPage() {
  const navigate = useNavigate();

  return (
    <div className="upload-page">
      <div className="workflow-intro">
        <span className="workflow-icon upload-workflow-icon">↥</span>
        <div>
          <h2>Bring your accounts into focus</h2>
          <p>Import a bank statement or transaction alerts to build your private financial overview.</p>
        </div>
      </div>
      <UploadStatement onUploaded={() => navigate("/")} />
    </div>
  );
}
