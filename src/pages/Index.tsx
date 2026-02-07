import { useNavigate } from "react-router-dom";
import { SearchSidebar } from "@/components/SearchSidebar";

const Index = () => {
  const navigate = useNavigate();

  return <SearchSidebar onStartShopping={() => navigate("/cart")} />;
};

export default Index;
