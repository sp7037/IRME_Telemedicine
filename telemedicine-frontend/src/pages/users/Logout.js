import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../../api/users";

const Logout = () => {
  const navigate = useNavigate();

  useEffect(() => {
    logoutUser();
    navigate("/login", { replace: true });
  }, [navigate]);

  return null;
};

export default Logout;

