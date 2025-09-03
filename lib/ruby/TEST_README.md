# Ruby Test Suite Documentation

## Overview

This test suite provides comprehensive testing for the Image Captioning Assistant Ruby library. It includes unit tests, integration tests, factories, fixtures, and continuous integration support.

## Test Structure

```
lib/ruby/
├── spec/
│   ├── spec_helper.rb                    # RSpec configuration
│   ├── factories/                        # FactoryBot factories
│   │   └── data_factories.rb             # Data model factories
│   ├── fixtures/                         # Test fixtures
│   │   ├── sample_metadata.json          # Sample metadata
│   │   └── sample_bias_response.json     # Sample bias analysis
│   ├── integration/                      # Integration tests
│   │   └── end_to_end_spec.rb           # End-to-end workflow tests
│   └── image_captioning_assistant/       # Unit tests
│       ├── aws/
│       │   └── s3_spec.rb               # S3 module tests
│       ├── client/
│       │   └── client_utils_spec.rb     # API client tests
│       ├── data/
│       │   ├── constants_spec.rb        # Constants tests
│       │   └── data_classes_spec.rb     # Data classes tests
│       └── generate/
│           └── utils_spec.rb             # Generation utilities tests
├── .rspec                                # RSpec options
├── Gemfile                               # Ruby dependencies
├── Rakefile                              # Rake tasks
└── run_tests.sh                          # Test runner script
```

## Setup

### Prerequisites

- Ruby 3.0+ installed
- Bundler gem installed (`gem install bundler`)
- ImageMagick installed (for image processing tests)

### Installation

```bash
cd lib/ruby
bundle install
```

## Running Tests

### Using the Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh unit

# Run only integration tests
./run_tests.sh integration

# Run tests with coverage report
./run_tests.sh coverage

# Run RuboCop linter
./run_tests.sh rubocop

# Run full CI suite
./run_tests.sh ci
```

### Using Rake Tasks

```bash
# Run all tests
bundle exec rake spec

# Run unit tests only
bundle exec rake spec:unit

# Run integration tests only
bundle exec rake spec:integration

# Run tests with coverage
bundle exec rake spec:coverage

# Run RuboCop
bundle exec rake rubocop

# Auto-correct RuboCop issues
bundle exec rake rubocop:auto_correct

# Run CI suite (tests + linting)
bundle exec rake ci
```

### Using RSpec Directly

```bash
# Run all tests
bundle exec rspec

# Run specific test file
bundle exec rspec spec/image_captioning_assistant/aws/s3_spec.rb

# Run tests matching a pattern
bundle exec rspec --pattern "spec/**/*_utils*"

# Run with specific format
bundle exec rspec --format documentation
```

## Test Coverage

The test suite uses SimpleCov for code coverage analysis. Coverage reports are generated in the `coverage/` directory when running:

```bash
bundle exec rake spec:coverage
```

View the coverage report by opening `coverage/index.html` in a browser.

## Writing Tests

### Unit Tests

Unit tests should be placed in `spec/image_captioning_assistant/` mirroring the source code structure. Example:

```ruby
RSpec.describe ImageCaptioningAssistant::AWS::S3 do
  describe '.parse_s3_uri' do
    it 'parses bucket and key correctly' do
      bucket, key = described_class.parse_s3_uri('s3://my-bucket/file.jpg')
      expect(bucket).to eq('my-bucket')
      expect(key).to eq('file.jpg')
    end
  end
end
```

### Using Factories

FactoryBot factories are available for creating test data:

```ruby
# Create a metadata object
metadata = FactoryBot.build(:metadata)

# Create a bias analysis with high biases
analysis = FactoryBot.build(:work_bias_analysis, :high_biases)

# Create multiple biases
biases = FactoryBot.build_list(:bias, 3, :medium)
```

### Using Fixtures

Load fixture files in your tests:

```ruby
# Load JSON fixture
metadata_json = load_fixture('sample_metadata.json')

# Load binary fixture
image_bytes = load_binary_fixture('test_image.jpg')
```

### Mocking AWS Services

Use WebMock to stub AWS service calls:

```ruby
# Stub S3 get_object
stub_request(:get, /s3\.amazonaws\.com/)
  .to_return(body: 'file content')

# Stub with specific bucket/key
s3_client = instance_double(Aws::S3::Client)
allow(Aws::S3::Client).to receive(:new).and_return(s3_client)
allow(s3_client).to receive(:get_object).and_return(response)
```

## Continuous Integration

The test suite includes GitHub Actions workflow configuration for CI. Tests run automatically on:

- Push to main or develop branches
- Pull requests to main or develop branches

CI runs tests against Ruby versions 3.0, 3.1, and 3.2.

## Test Helpers

The `spec_helper.rb` provides several helper methods:

- `stub_aws_credentials` - Stubs AWS environment variables
- `create_test_image_bytes` - Creates a minimal JPEG for testing
- `fixture_path(filename)` - Returns path to fixture file
- `load_fixture(filename)` - Loads text fixture
- `load_binary_fixture(filename)` - Loads binary fixture

## Debugging

### Interactive Console

Open a console with the library loaded:

```bash
bundle exec rake console
```

### Using Pry

Add breakpoints in your tests:

```ruby
require 'pry'

it 'does something' do
  binding.pry  # Execution stops here
  expect(result).to eq(expected)
end
```

## Best Practices

1. **Isolate Tests**: Each test should be independent and not rely on other tests
2. **Use Factories**: Prefer factories over manually creating test data
3. **Mock External Services**: Always mock AWS and external API calls
4. **Test Edge Cases**: Include tests for nil values, empty arrays, and error conditions
5. **Keep Tests Fast**: Use mocks/stubs instead of real network calls
6. **Clear Descriptions**: Use descriptive test names that explain what is being tested

## Troubleshooting

### Bundle Install Fails

If ImageMagick dependencies fail:

```bash
# macOS
brew install imagemagick

# Ubuntu/Debian
sudo apt-get install imagemagick libmagickwand-dev

# RHEL/CentOS
sudo yum install ImageMagick ImageMagick-devel
```

### Tests Fail with Network Errors

Ensure all external calls are properly mocked:

```ruby
before do
  WebMock.disable_net_connect!(allow_localhost: true)
end
```

### Coverage Report Not Generated

Ensure SimpleCov is loaded before any application code:

```ruby
# In spec_helper.rb (at the top)
require 'simplecov'
SimpleCov.start
```

## Contributing

1. Write tests for any new functionality
2. Ensure all tests pass before submitting PR
3. Maintain or improve code coverage
4. Follow RuboCop style guidelines
5. Update this documentation for significant changes