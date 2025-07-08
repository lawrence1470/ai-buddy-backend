# Generate TypeScript Types from OpenAPI for React Native Expo

## 🚀 **Method 1: openapi-typescript (Recommended)**

### 1. Install in your Expo project

```bash
# In your Expo/React Native project directory
npm install -D openapi-typescript
# or
yarn add -D openapi-typescript
```

### 2. Add scripts to package.json

```json
{
  "scripts": {
    "generate-types": "openapi-typescript http://localhost:8080/swagger.json --output ./src/types/api.ts",
    "generate-types:prod": "openapi-typescript https://your-api-domain.com/swagger.json --output ./src/types/api.ts"
  }
}
```

### 3. Generate types

```bash
# Make sure your API server is running on localhost:8080
npm run generate-types
```

### 4. Usage in React Native/Expo

Create `src/types/api.ts` (auto-generated) and use like this:

```typescript
// src/hooks/useApi.ts
import type { paths, components } from "../types/api";

// Extract schema types
type HealthStatus = components["schemas"]["HealthStatus"];
type SessionRequest = components["schemas"]["SessionRequest"];
type PersonalityProfile = components["schemas"]["PersonalityProfile"];
type SessionProcessResult = components["schemas"]["SessionProcessResult"];

// Extract API endpoint types
type ApiPaths = paths;
type GetHealthResponse =
  ApiPaths["/health"]["get"]["responses"]["200"]["content"]["application/json"];
type ProcessSessionRequest =
  ApiPaths["/sessions/process"]["post"]["requestBody"]["content"]["application/json"];
type ProcessSessionResponse =
  ApiPaths["/sessions/process"]["post"]["responses"]["200"]["content"]["application/json"];

// Example API hook
export const usePersonalityApi = () => {
  const processSession = async (
    data: SessionRequest
  ): Promise<SessionProcessResult> => {
    const response = await fetch("http://localhost:8080/sessions/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer your-token",
      },
      body: JSON.stringify(data),
    });
    return response.json();
  };

  const getPersonality = async (
    userId: string
  ): Promise<PersonalityProfile> => {
    const response = await fetch(
      `http://localhost:8080/personality/${userId}`,
      {
        headers: {
          Authorization: "Bearer your-token",
        },
      }
    );
    return response.json();
  };

  const getHealth = async (): Promise<HealthStatus> => {
    const response = await fetch("http://localhost:8080/health");
    return response.json();
  };

  return { processSession, getPersonality, getHealth };
};
```

### 5. React Native Component Example

```typescript
// src/screens/PersonalityScreen.tsx
import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { usePersonalityApi } from "../hooks/useApi";
import type { components } from "../types/api";

type PersonalityProfile = components["schemas"]["PersonalityProfile"];

export const PersonalityScreen: React.FC<{ userId: string }> = ({ userId }) => {
  const [personality, setPersonality] = useState<PersonalityProfile | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const api = usePersonalityApi();

  useEffect(() => {
    const fetchPersonality = async () => {
      try {
        const data = await api.getPersonality(userId);
        setPersonality(data);
      } catch (error) {
        console.error("Error fetching personality:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPersonality();
  }, [userId]);

  if (loading) return <Text>Loading...</Text>;
  if (!personality) return <Text>No personality data found</Text>;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Personality Profile</Text>
      <Text style={styles.mbtiType}>{personality.mbti_type}</Text>
      <Text style={styles.description}>{personality.type_description}</Text>
      <Text style={styles.confidence}>
        Confidence: {Math.round((personality.confidence_score || 0) * 100)}%
      </Text>

      <View style={styles.traitsContainer}>
        <Text style={styles.traitsTitle}>Trait Scores:</Text>
        {personality.trait_scores &&
          Object.entries(personality.trait_scores).map(([trait, score]) => (
            <Text key={trait} style={styles.trait}>
              {trait}: {Math.round((score as number) * 100)}%
            </Text>
          ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { padding: 20 },
  title: { fontSize: 24, fontWeight: "bold", marginBottom: 10 },
  mbtiType: { fontSize: 20, color: "#007AFF", marginBottom: 5 },
  description: { fontSize: 16, marginBottom: 10 },
  confidence: { fontSize: 14, color: "#666", marginBottom: 20 },
  traitsContainer: { marginTop: 20 },
  traitsTitle: { fontSize: 18, fontWeight: "bold", marginBottom: 10 },
  trait: { fontSize: 14, marginBottom: 5 },
});
```

## 🛠️ **Method 2: Auto-generation with GitHub Actions**

Create `.github/workflows/generate-types.yml`:

```yaml
name: Generate API Types

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  generate-types:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"

      - name: Install dependencies
        run: npm ci

      - name: Generate API types
        run: npm run generate-types:prod

      - name: Commit updated types
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add src/types/api.ts
          git diff --staged --quiet || git commit -m "Auto-update API types"
          git push
```

## 🔧 **Advanced Configuration**

Create `openapi-ts.config.ts`:

```typescript
import { defineConfig } from "openapi-typescript";

export default defineConfig({
  // Input OpenAPI schema
  input: "http://localhost:8000/swagger.json",

  // Output TypeScript file
  output: "./src/types/api.ts",

  // Additional options
  exportType: true,
  enum: true,
  immutable: true,

  // Transform schema names
  transform: {
    schemaName: (name: string) => {
      // Convert PascalCase to more readable names
      return name.replace(/([A-Z])/g, " $1").trim();
    },
  },
});
```

Then run: `npx openapi-typescript --config openapi-ts.config.ts`

## 📱 **Expo-specific Tips**

1. **Environment Variables**: Use `app.config.js` for API URLs:

```javascript
// app.config.js
export default {
  expo: {
    extra: {
      apiUrl:
        process.env.NODE_ENV === "development"
          ? "http://localhost:8000"
          : "https://your-api.com",
    },
  },
};
```

2. **Use in your app**:

```typescript
import Constants from "expo-constants";

const API_URL = Constants.expoConfig?.extra?.apiUrl || "http://localhost:8000";
```

3. **Development workflow**:

```bash
# Terminal 1: Start your API
cd ai-backend
python3 api_docs_app.py

# Terminal 2: Generate types and start Expo
cd your-expo-app
npm run generate-types
npx expo start
```

## ✅ **Benefits**

- **Type Safety**: Full TypeScript support for all API calls
- **Auto-completion**: VS Code will autocomplete API properties
- **Error Prevention**: Catch API mismatches at compile time
- **Always in Sync**: Types match your actual API schema
- **Zero Maintenance**: Automatically updates when API changes

This setup will give you complete type safety between your AI Personality Backend and your React Native Expo app! 🚀
