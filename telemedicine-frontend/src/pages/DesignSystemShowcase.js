import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Button,
  Input,
  Select,
  Card,
  Alert,
  Badge,
  Modal,
  Spinner,
  Container,
} from "../components/ui";
import LanguageSwitcher from "../components/LanguageSwitcher";
import StatusBadge from "../components/dashboard/StatusBadge";
import theme from "../theme/tokens";

/**
 * Design System Showcase Page
 * This page demonstrates all UI components in the design system
 */
const DesignSystemShowcase = () => {
  const { t } = useTranslation();
  const [modalOpen, setModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [selectValue, setSelectValue] = useState("option1");

  const pageStyles = {
    minHeight: "100vh",
    background: theme.gradients.dashboardPage,
    padding: `${theme.spacing[8]} 0`,
  };

  const sectionStyles = {
    marginBottom: theme.spacing[12],
  };

  const headingStyles = {
    fontSize: theme.typography.fontSize["3xl"],
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing[4],
  };

  const subheadingStyles = {
    fontSize: theme.typography.fontSize["2xl"],
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing[4],
    marginTop: theme.spacing[8],
  };

  const gridStyles = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: theme.spacing[4],
    marginBottom: theme.spacing[6],
  };

  return (
    <div style={pageStyles}>
      <Container maxWidth="xl">
        <h1 style={headingStyles}>IRME Telemedicine Design System</h1>
        <p style={{ color: theme.colors.text.secondary, marginBottom: theme.spacing[8] }}>
          Comprehensive showcase of all UI components, design tokens, and internationalization features.
        </p>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Language Switcher</h2>
            <div style={{ display: "flex", gap: theme.spacing[4], alignItems: "center", flexWrap: "wrap" }}>
              <div>
                <p style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.fontSize.sm }}>Full mode:</p>
                <LanguageSwitcher />
              </div>
              <div>
                <p style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.fontSize.sm }}>Compact mode:</p>
                <LanguageSwitcher compact />
              </div>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Buttons</h2>
            <div style={gridStyles}>
              <Button variant="primary">{t("common.submit")}</Button>
              <Button variant="secondary">{t("common.save")}</Button>
              <Button variant="success">{t("common.confirm")}</Button>
              <Button variant="danger">{t("common.delete")}</Button>
              <Button variant="outline">{t("common.cancel")}</Button>
              <Button variant="ghost">{t("common.close")}</Button>
            </div>

            <h3 style={{ ...subheadingStyles, fontSize: theme.typography.fontSize.xl, marginTop: theme.spacing[6] }}>
              Sizes
            </h3>
            <div style={{ display: "flex", gap: theme.spacing[4], alignItems: "center", flexWrap: "wrap" }}>
              <Button size="sm">Small</Button>
              <Button size="md">Medium</Button>
              <Button size="lg">Large</Button>
            </div>

            <h3 style={{ ...subheadingStyles, fontSize: theme.typography.fontSize.xl, marginTop: theme.spacing[6] }}>
              States
            </h3>
            <div style={{ display: "flex", gap: theme.spacing[4], alignItems: "center", flexWrap: "wrap" }}>
              <Button disabled>{t("common.submit")}</Button>
              <Button loading>{t("common.loading")}</Button>
              <Button fullWidth>{t("common.submit")} (Full width)</Button>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Form Inputs</h2>
            <div style={{ display: "grid", gap: theme.spacing[6] }}>
              <Input
                label={t("auth.email")}
                type="email"
                placeholder="user@example.com"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                fullWidth
              />
              <Input
                label={t("auth.password")}
                type="password"
                placeholder={t("auth.password")}
                helperText="Must be at least 8 characters"
                fullWidth
              />
              <Input
                label="Input with error"
                type="text"
                error={t("errors.required")}
                fullWidth
              />
              <Select
                label="Select dropdown"
                options={[
                  { value: "option1", label: "Option 1" },
                  { value: "option2", label: "Option 2" },
                  { value: "option3", label: "Option 3" },
                ]}
                value={selectValue}
                onChange={(e) => setSelectValue(e.target.value)}
                fullWidth
              />
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Alerts</h2>
            <div style={{ display: "grid", gap: theme.spacing[4] }}>
              <Alert variant="info">
                This is an informational message.
              </Alert>
              <Alert variant="success">
                {t("messages.saveSuccess")}
              </Alert>
              <Alert variant="warning">
                Your session will expire soon.
              </Alert>
              <Alert variant="error" dismissible onDismiss={() => console.log("Dismissed")}>
                {t("errors.generic")}
              </Alert>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Badges</h2>
            <div style={{ display: "flex", gap: theme.spacing[3], alignItems: "center", flexWrap: "wrap" }}>
              <Badge variant="default">Default</Badge>
              <Badge variant="primary">Primary</Badge>
              <Badge variant="success">Success</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="error">Error</Badge>
              <Badge variant="info">Info</Badge>
            </div>

            <h3 style={{ ...subheadingStyles, fontSize: theme.typography.fontSize.xl, marginTop: theme.spacing[6] }}>
              Sizes
            </h3>
            <div style={{ display: "flex", gap: theme.spacing[3], alignItems: "center", flexWrap: "wrap" }}>
              <Badge size="sm">Small</Badge>
              <Badge size="md">Medium</Badge>
              <Badge size="lg">Large</Badge>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Status Badges (Consultation States)</h2>
            <div style={{ display: "flex", gap: theme.spacing[3], alignItems: "center", flexWrap: "wrap" }}>
              <StatusBadge status="PENDING" />
              <StatusBadge status="ACCEPTED" />
              <StatusBadge status="QUEUED" />
              <StatusBadge status="IN_PROGRESS" />
              <StatusBadge status="COMPLETED" />
              <StatusBadge status="REJECTED" />
              <StatusBadge status="POSTPONED" />
              <StatusBadge status="CANCELED" />
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Cards</h2>
            <div style={gridStyles}>
              <Card padding="sm">
                <h4 style={{ margin: 0, marginBottom: theme.spacing[2] }}>Small Padding</h4>
                <p style={{ margin: 0, fontSize: theme.typography.fontSize.sm }}>Card content</p>
              </Card>
              <Card padding="md">
                <h4 style={{ margin: 0, marginBottom: theme.spacing[2] }}>Medium Padding</h4>
                <p style={{ margin: 0, fontSize: theme.typography.fontSize.sm }}>Card content</p>
              </Card>
              <Card padding="lg" hoverable>
                <h4 style={{ margin: 0, marginBottom: theme.spacing[2] }}>Large Padding + Hoverable</h4>
                <p style={{ margin: 0, fontSize: theme.typography.fontSize.sm }}>Hover to see effect</p>
              </Card>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Modal</h2>
            <Button onClick={() => setModalOpen(true)}>Open Modal</Button>
            <Modal
              isOpen={modalOpen}
              onClose={() => setModalOpen(false)}
              title="Example Modal"
              size="md"
              footer={
                <>
                  <Button variant="ghost" onClick={() => setModalOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                  <Button variant="primary" onClick={() => setModalOpen(false)}>
                    {t("common.confirm")}
                  </Button>
                </>
              }
            >
              <p>This is an example modal dialog. It demonstrates the modal component with a title, body content, and footer actions.</p>
              <p>You can close it by clicking the X button, clicking outside, or pressing Escape.</p>
            </Modal>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Loading Spinner</h2>
            <div style={{ display: "flex", gap: theme.spacing[8], alignItems: "center", flexWrap: "wrap" }}>
              <div>
                <p style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.fontSize.sm }}>Small</p>
                <Spinner size="sm" />
              </div>
              <div>
                <p style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.fontSize.sm }}>Medium</p>
                <Spinner size="md" />
              </div>
              <div>
                <p style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.fontSize.sm }}>Large</p>
                <Spinner size="lg" />
              </div>
            </div>
          </Card>
        </section>

        <section style={sectionStyles}>
          <Card>
            <h2 style={subheadingStyles}>Design Tokens</h2>
            <div style={{ display: "grid", gap: theme.spacing[6] }}>
              <div>
                <h3 style={{ fontSize: theme.typography.fontSize.lg, marginBottom: theme.spacing[3] }}>Colors</h3>
                <div style={gridStyles}>
                  {Object.entries({
                    Primary: theme.colors.primary,
                    Secondary: theme.colors.secondary,
                    Success: theme.colors.success,
                    Warning: theme.colors.warning,
                    Error: theme.colors.error,
                    Info: theme.colors.info,
                  }).map(([name, color]) => (
                    <div key={name} style={{ textAlign: "center" }}>
                      <div
                        style={{
                          width: "100%",
                          height: "60px",
                          backgroundColor: color,
                          borderRadius: theme.radii.md,
                          marginBottom: theme.spacing[2],
                        }}
                      />
                      <p style={{ fontSize: theme.typography.fontSize.sm, margin: 0 }}>{name}</p>
                      <p style={{ fontSize: theme.typography.fontSize.xs, color: theme.colors.text.tertiary, margin: 0 }}>
                        {color}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: theme.typography.fontSize.lg, marginBottom: theme.spacing[3] }}>Typography</h3>
                <div style={{ display: "grid", gap: theme.spacing[3] }}>
                  {Object.entries({
                    xs: theme.typography.fontSize.xs,
                    sm: theme.typography.fontSize.sm,
                    base: theme.typography.fontSize.base,
                    lg: theme.typography.fontSize.lg,
                    xl: theme.typography.fontSize.xl,
                    "2xl": theme.typography.fontSize["2xl"],
                    "3xl": theme.typography.fontSize["3xl"],
                  }).map(([size, value]) => (
                    <p key={size} style={{ fontSize: value, margin: 0 }}>
                      {size} ({value}) - The quick brown fox
                    </p>
                  ))}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: theme.typography.fontSize.lg, marginBottom: theme.spacing[3] }}>Spacing</h3>
                <div style={{ display: "grid", gap: theme.spacing[2] }}>
                  {Object.entries({
                    1: theme.spacing[1],
                    2: theme.spacing[2],
                    3: theme.spacing[3],
                    4: theme.spacing[4],
                    5: theme.spacing[5],
                    6: theme.spacing[6],
                    8: theme.spacing[8],
                  }).map(([size, value]) => (
                    <div key={size} style={{ display: "flex", alignItems: "center", gap: theme.spacing[3] }}>
                      <span style={{ fontSize: theme.typography.fontSize.sm, minWidth: "60px" }}>
                        {size} ({value})
                      </span>
                      <div
                        style={{
                          width: value,
                          height: "24px",
                          backgroundColor: theme.colors.primary,
                          borderRadius: theme.radii.sm,
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </section>
      </Container>
    </div>
  );
};

export default DesignSystemShowcase;
