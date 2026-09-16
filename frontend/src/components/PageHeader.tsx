import React from "react";

interface PageHeaderProps {
  category?: string;
  title: string;
  subtitle?: string;
  badge?: string;
  actions?: React.ReactNode;
}

export default function PageHeader({
  category = "AGNINETRA MONITORING PORTAL",
  title,
  subtitle,
  badge,
  actions,
}: PageHeaderProps) {
  return (
    <div className="portal-page-header">
      <div className="header-text-col">
        {category && <span className="header-category">{category}</span>}
        <div className="header-title-row">
          <h1 className="header-main-title">{title}</h1>
          {badge && <span className="header-status-badge">{badge}</span>}
        </div>
        {subtitle && <p className="header-subtitle">{subtitle}</p>}
      </div>

      {actions && <div className="header-actions-col">{actions}</div>}
    </div>
  );
}
