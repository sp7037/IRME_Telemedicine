# IRME Telemedicine Design System

This document describes the design system implementation for the IRME Telemedicine React frontend.

## Overview

The design system provides:
- **Centralized design tokens** (colors, typography, spacing, shadows, etc.)
- **Reusable UI components** with consistent styling
- **Multi-language support** (English, Hindi, Marathi)
- **Responsive layouts** for mobile, tablet, and desktop
- **Accessibility features** (ARIA labels, keyboard navigation, focus states)

## Design Tokens

Design tokens are defined in `src/theme/tokens.js`. Import them as:

```javascript
import theme from '../theme/tokens';
// or destructure specific sections
import { colors, typography, spacing } from '../theme/tokens';
```

### Available Tokens

- **colors**: Brand colors, semantic colors (primary, success, error, etc.), gray palette, text/background/border colors, status colors
- **typography**: Font families, sizes, weights, line heights, letter spacing
- **spacing**: Consistent spacing scale (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24)
- **shadows**: Shadow scale from sm to 2xl, plus focus shadow
- **radii**: Border radius values (none, sm, base, md, lg, xl, 2xl, full)
- **breakpoints**: Responsive breakpoints (xs: 480px, sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px)
- **zIndex**: Z-index scale for layering (dropdown, sticky, modal, tooltip, etc.)
- **transitions**: Timing for animations (fast: 150ms, base: 200ms, slow: 300ms)
- **gradients**: Pre-defined gradient backgrounds

### Usage Example

```javascript
import theme from '../theme/tokens';

const styles = {
  container: {
    padding: theme.spacing[6],
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.radii.lg,
    boxShadow: theme.shadows.md,
  },
  title: {
    fontSize: theme.typography.fontSize['2xl'],
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
  }
};
```

## UI Components

Reusable components are in `src/components/ui/`. Import them as:

```javascript
import { Button, Card, Input, Alert } from '../components/ui';
```

### Button

Flexible button component with variants and sizes.

```javascript
<Button variant="primary" size="md" onClick={handleClick}>
  Click me
</Button>

<Button variant="success" size="lg" fullWidth>
  Submit
</Button>

<Button variant="outline" disabled>
  Disabled
</Button>

<Button variant="danger" loading>
  Processing...
</Button>
```

**Props:**
- `variant`: "primary" | "secondary" | "success" | "danger" | "outline" | "ghost" (default: "primary")
- `size`: "sm" | "md" | "lg" (default: "md")
- `fullWidth`: boolean (default: false)
- `disabled`: boolean (default: false)
- `loading`: boolean (default: false)
- `onClick`, `type`, `style`, `className`, and other standard button props

### Input

Text input with label, error, and helper text.

```javascript
<Input
  label="Email"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  required
  fullWidth
/>

<Input
  label="Password"
  type="password"
  error="Password must be at least 8 characters"
  helperText="Choose a strong password"
/>
```

**Props:**
- `type`: "text" | "email" | "password" | "number" | "tel" | "search" | "url" (default: "text")
- `label`: string (optional)
- `error`: string (displays error message)
- `helperText`: string (displays helper text when no error)
- `required`: boolean (default: false)
- `disabled`: boolean (default: false)
- `fullWidth`: boolean (default: false)
- Standard input props: `value`, `onChange`, `placeholder`, etc.

### Select

Dropdown select with label and error state.

```javascript
<Select
  label="Country"
  options={[
    { value: "in", label: "India" },
    { value: "us", label: "United States" },
  ]}
  value={country}
  onChange={(e) => setCountry(e.target.value)}
  required
  fullWidth
/>
```

**Props:**
- `label`: string (optional)
- `options`: Array<{value: string, label: string}> (required)
- `error`: string (displays error message)
- `required`: boolean (default: false)
- `disabled`: boolean (default: false)
- `fullWidth`: boolean (default: false)
- Standard select props: `value`, `onChange`, etc.

### Card

Container component for grouping content.

```javascript
<Card padding="md" hoverable>
  <h3>Card Title</h3>
  <p>Card content goes here</p>
</Card>

<Card padding="lg" onClick={handleCardClick}>
  Clickable card
</Card>
```

**Props:**
- `padding`: "none" | "sm" | "md" | "lg" (default: "md")
- `hoverable`: boolean (adds hover effect, default: false)
- `onClick`: function (makes card clickable)
- `style`, `className`, and other standard div props

### Alert

Alert/notification component for messages.

```javascript
<Alert variant="success">
  Your changes have been saved!
</Alert>

<Alert variant="error" dismissible onDismiss={handleDismiss}>
  An error occurred. Please try again.
</Alert>

<Alert variant="warning">
  Your session will expire in 5 minutes.
</Alert>
```

**Props:**
- `variant`: "info" | "success" | "warning" | "error" (default: "info")
- `dismissible`: boolean (shows dismiss button, default: false)
- `onDismiss`: function (called when dismiss button is clicked)
- `children`: React node (alert content)
- `style`, `className`

### Badge

Small status indicator or label.

```javascript
<Badge variant="primary">New</Badge>
<Badge variant="success" size="sm">Active</Badge>
<Badge variant="error" size="lg">Failed</Badge>
```

**Props:**
- `variant`: "default" | "primary" | "success" | "warning" | "error" | "info" (default: "default")
- `size`: "sm" | "md" | "lg" (default: "md")
- `children`: React node
- `style`, `className`

### Modal

Modal dialog overlay.

```javascript
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  size="md"
  footer={
    <>
      <Button variant="ghost" onClick={handleClose}>Cancel</Button>
      <Button variant="primary" onClick={handleConfirm}>Confirm</Button>
    </>
  }
>
  <p>Are you sure you want to proceed?</p>
</Modal>
```

**Props:**
- `isOpen`: boolean (required, controls visibility)
- `onClose`: function (required, called when modal should close)
- `title`: string (optional, modal title)
- `footer`: React node (optional, modal footer content)
- `size`: "sm" | "md" | "lg" | "xl" (default: "md")
- `children`: React node (modal body content)
- `style`, `className`

### Spinner

Loading spinner.

```javascript
<Spinner size="md" />
<Spinner size="lg" color="#ff0000" />
```

**Props:**
- `size`: "sm" | "md" | "lg" (default: "md")
- `color`: string (optional, defaults to theme primary color)
- `style`, `className`

## Internationalization (i18n)

The app supports three languages:
- **English (en)** - Default
- **Hindi (hi)** - हिंदी
- **Marathi (mr)** - मराठी

### Setup

i18n is configured in `src/i18n/config.js` using `react-i18next`. It automatically detects the user's language preference and persists it in localStorage.

### Using Translations

Import and use the `useTranslation` hook:

```javascript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('home.heroTitle')}</h1>
      <p>{t('home.heroSubtitle')}</p>
      <button>{t('common.submit')}</button>
    </div>
  );
}
```

### Translation Files

Translation files are in `src/i18n/locales/`:
- `en.json` - English
- `hi.json` - Hindi
- `mr.json` - Marathi

Organized by namespace:
- `common` - Common UI elements (buttons, labels, etc.)
- `nav` - Navigation items
- `auth` - Authentication (login, signup, etc.)
- `user` - User-related fields
- `consultation` - Consultation workflow
- `doctor` - Doctor-specific terms
- `wallet` - Wallet/payment terms
- `tmc` - TMC-specific terms
- `admin` - Admin interface
- `errors` - Error messages
- `messages` - Success/info messages
- `home` - Home page content
- `language` - Language selection

### Adding New Translations

1. Add the key-value pair to `en.json`:
   ```json
   {
     "myNamespace": {
       "myKey": "My English text"
     }
   }
   ```

2. Add translations to `hi.json` and `mr.json`:
   ```json
   {
     "myNamespace": {
       "myKey": "मेरा हिंदी पाठ"
     }
   }
   ```

3. Use in component:
   ```javascript
   const { t } = useTranslation();
   return <p>{t('myNamespace.myKey')}</p>;
   ```

### Interpolation

For dynamic values:

```javascript
// In translation file:
{
  "greeting": "Hello, {{name}}!"
}

// In component:
t('greeting', { name: 'John' })
// Output: "Hello, John!"
```

### Language Switcher

A `LanguageSwitcher` component is provided:

```javascript
import LanguageSwitcher from '../components/LanguageSwitcher';

<LanguageSwitcher />           {/* Full dropdown */}
<LanguageSwitcher compact />   {/* Compact with language codes */}
```

The language switcher is already integrated into the dashboard Header.

## Responsive Design

Use the `breakpoints` from theme tokens for responsive layouts:

```javascript
import theme from '../theme/tokens';

const styles = {
  container: {
    padding: theme.spacing[4],
    // Mobile-first: stack on small screens
    display: 'flex',
    flexDirection: 'column',
  },
};

// Use CSS media queries for larger screens
const desktopStyles = `
  @media (min-width: ${theme.breakpoints.md}) {
    .container {
      flex-direction: row;
      padding: ${theme.spacing[8]};
    }
  }
`;
```

For inline styles, check window width:

```javascript
const isMobile = window.innerWidth < 768;
const styles = {
  container: {
    padding: isMobile ? theme.spacing[4] : theme.spacing[8],
  }
};
```

## Accessibility

All design system components include accessibility features:

- **Semantic HTML**: Proper use of elements (button, input, label, etc.)
- **ARIA labels**: All interactive elements have aria-label or aria-labelledby
- **Focus states**: Visible focus indicators for keyboard navigation
- **Color contrast**: Text colors meet WCAG AA standards
- **Form labels**: All inputs have associated labels
- **Keyboard navigation**: All interactive elements are keyboard accessible
- **Screen reader support**: Proper role and aria attributes

### Best Practices

1. Always provide labels for form inputs
2. Use semantic HTML elements
3. Add aria-label to icon-only buttons
4. Ensure sufficient color contrast
5. Test with keyboard navigation
6. Use focus-visible styles

## Migration Guide

To migrate existing components to the design system:

### 1. Replace inline color values with theme colors

**Before:**
```javascript
const styles = {
  text: { color: '#10243e' }
};
```

**After:**
```javascript
import theme from '../theme/tokens';

const styles = {
  text: { color: theme.colors.text.primary }
};
```

### 2. Use UI components instead of custom styled elements

**Before:**
```javascript
<button style={{ padding: '10px 20px', background: '#1f76d8', color: '#fff' }}>
  Click me
</button>
```

**After:**
```javascript
import { Button } from '../components/ui';

<Button variant="primary">Click me</Button>
```

### 3. Add i18n to static text

**Before:**
```javascript
<h1>Dashboard</h1>
<button>Submit</button>
```

**After:**
```javascript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t('nav.dashboard')}</h1>
      <button>{t('common.submit')}</button>
    </>
  );
}
```

### 4. Use consistent spacing

**Before:**
```javascript
const styles = {
  container: { padding: '24px', gap: '16px' }
};
```

**After:**
```javascript
import theme from '../theme/tokens';

const styles = {
  container: {
    padding: theme.spacing[6],  // 24px
    gap: theme.spacing[4]        // 16px
  }
};
```

## Testing

After making changes:

1. **Build the app**: `npm run build`
2. **Run the dev server**: `npm start`
3. **Test all languages**: Use the language switcher to verify translations
4. **Test responsive layouts**: Resize browser to check mobile/tablet/desktop views
5. **Test keyboard navigation**: Tab through forms and interactive elements
6. **Test accessibility**: Use screen reader or browser dev tools

## Future Enhancements

Potential improvements:
- Dark mode support
- Additional language support
- CSS-in-JS library integration (styled-components, emotion)
- Component variants system
- Animation utilities
- Form validation helpers
- Toast notification system
- Data table component
- Date picker component
- File upload component
