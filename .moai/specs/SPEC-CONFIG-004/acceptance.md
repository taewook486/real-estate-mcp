# Acceptance Criteria: SPEC-CONFIG-004

## Test Scenarios

### Scenario 1: Valid Configuration Loading

**Given** all required environment variables are set correctly
**When** the application loads the configuration
**Then** `AppSettings` should initialize without errors
**And** all API keys should be accessible via properties

```gherkin
Scenario: Load valid configuration
  Given environment variable DATA_GO_KR_API_KEY is set to "test-key-123"
  And environment variable ONBID_API_KEY is set to "onbid-key-456"
  When I create an AppSettings instance
  Then the instance should be created successfully
  And data_go_kr_api_key should equal "test-key-123"
  And get_onbid_key() should return "onbid-key-456"
```

### Scenario 2: Missing Required Configuration

**Given** required environment variable DATA_GO_KR_API_KEY is not set
**When** the application attempts to load configuration
**Then** a clear error message should be displayed
**And** the error should include setup instructions

```gherkin
Scenario: Missing required API key
  Given environment variable DATA_GO_KR_API_KEY is not set
  When I attempt to validate the settings
  Then a ValueError should be raised
  And the error message should contain "DATA_GO_KR_API_KEY is required"
  And the error message should contain "https://apis.data.go.kr"
```

### Scenario 3: Fallback Key Resolution

**Given** ONBID_API_KEY is not set
**And** DATA_GO_KR_API_KEY is set to "fallback-key"
**When** the application requests the Onbid API key
**Then** the system should return the DATA_GO_KR_API_KEY value as fallback

```gherkin
Scenario: Onbid key fallback
  Given environment variable DATA_GO_KR_API_KEY is set to "fallback-key"
  And environment variable ONBID_API_KEY is not set
  When I call get_onbid_key()
  Then the result should equal "fallback-key"
```

### Scenario 4: Odcloud Authentication Priority

**Given** multiple odcloud keys are configured
**When** the application requests odcloud authentication
**Then** the system should return keys in priority order (API_KEY > SERVICE_KEY > DATA_GO_KR)

```gherkin
Scenario: Odcloud authentication priority
  Given environment variable ODCLOUD_API_KEY is set to "api-key"
  And environment variable ODCLOUD_SERVICE_KEY is set to "service-key"
  And environment variable DATA_GO_KR_API_KEY is set to "data-key"
  When I call get_odcloud_auth()
  Then the result should be ("authorization", "api-key")
```

### Scenario 5: Integration with MCP Tools

**Given** the centralized configuration is implemented
**When** an MCP tool is invoked
**Then** it should use the centralized settings for API key validation
**And** error messages should be consistent across all tools

```gherkin
Scenario: MCP tool integration
  Given the centralized AppSettings is configured
  And DATA_GO_KR_API_KEY is not set
  When I call an MCP tool that requires API access
  Then the tool should return a config_error
  And the error message should reference the centralized settings
```

## Edge Cases

### Empty String Configuration

```gherkin
Scenario: Empty string API key
  Given environment variable DATA_GO_KR_API_KEY is set to ""
  When I attempt to validate the settings
  Then validation should fail
  And the error should indicate the key is empty
```

### Whitespace-Only Configuration

```gherkin
Scenario: Whitespace-only API key
  Given environment variable DATA_GO_KR_API_KEY is set to "   "
  When I attempt to validate the settings
  Then validation should fail
  And the key should be trimmed before validation
```

### Special Characters in Keys

```gherkin
Scenario: API key with special characters
  Given environment variable DATA_GO_KR_API_KEY contains URL-encoded characters
  When I create an AppSettings instance
  Then the key should be stored as-is without decoding
```

## Quality Gates

- [ ] All unit tests pass with 85%+ coverage
- [ ] Integration tests pass with all MCP tools
- [ ] No regression in existing functionality
- [ ] Error messages are clear and actionable
- [ ] Documentation updated with new configuration pattern

## Performance Criteria

- Configuration load time: < 10ms
- Memory overhead: < 1KB per settings instance
- No blocking I/O during configuration access
