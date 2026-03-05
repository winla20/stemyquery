import { createBrowserRouter } from "react-router";
import Layout from "./pages/Layout";
import ResearchMode from "./pages/ResearchMode";
import DiscoveryMode from "./pages/DiscoveryMode";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: ResearchMode },
      { path: "discovery", Component: DiscoveryMode },
    ],
  },
]);
