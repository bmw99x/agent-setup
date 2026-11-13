export type Plan = {
  id: string;
  name: string;
  monthlyPrice: string;
  features: string[];
};

export const PLANS: Plan[] = [
  { id: "starter", name: "Starter", monthlyPrice: "£9", features: ["1 workspace", "Email support", "30-day history"] },
  {
    id: "growth",
    name: "Growth",
    monthlyPrice: "£25",
    features: ["5 workspaces", "Priority email support", "1-year history", "Audit log"],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    monthlyPrice: "£99",
    features: ["Unlimited workspaces", "Dedicated account manager", "Unlimited history", "Audit log", "SSO"],
  },
];
