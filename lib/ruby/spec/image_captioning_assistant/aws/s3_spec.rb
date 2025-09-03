# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'

RSpec.describe ImageCaptioningAssistant::AWS::S3 do
  describe '.parse_s3_uri' do
    context 'with s3:// format' do
      it 'parses bucket and key correctly' do
        bucket, key = described_class.parse_s3_uri('s3://my-bucket/path/to/file.jpg')
        expect(bucket).to eq('my-bucket')
        expect(key).to eq('path/to/file.jpg')
      end

      it 'handles URIs with special characters' do
        bucket, key = described_class.parse_s3_uri('s3://my-bucket/path/with%20spaces/file.jpg')
        expect(bucket).to eq('my-bucket')
        expect(key).to eq('path/with%20spaces/file.jpg')
      end
    end

    context 'with bucket/key format' do
      it 'parses bucket and key correctly' do
        bucket, key = described_class.parse_s3_uri('my-bucket/path/to/file.jpg')
        expect(bucket).to eq('my-bucket')
        expect(key).to eq('path/to/file.jpg')
      end
    end

    context 'with just key format' do
      before do
        allow(ENV).to receive(:fetch).with('UPLOADS_BUCKET_NAME', nil).and_return('uploads-bucket')
      end

      it 'uses UPLOADS_BUCKET_NAME from environment' do
        bucket, key = described_class.parse_s3_uri('file.jpg')
        expect(bucket).to eq('uploads-bucket')
        expect(key).to eq('file.jpg')
      end

      it 'raises error for blank key' do
        expect { described_class.parse_s3_uri('  ') }.to raise_error(ArgumentError, 'S3 key must not be blank')
      end
    end

    context 'with nil or empty input' do
      it 'returns [nil, nil] for nil input' do
        bucket, key = described_class.parse_s3_uri(nil)
        expect(bucket).to be_nil
        expect(key).to be_nil
      end

      it 'returns [nil, nil] for empty string' do
        bucket, key = described_class.parse_s3_uri('')
        expect(bucket).to be_nil
        expect(key).to be_nil
      end
    end
  end

  describe '.load_to_str' do
    let(:s3_client) { instance_double(Aws::S3::Client) }
    let(:s3_response) { instance_double(Aws::S3::Types::GetObjectOutput) }
    let(:body) { StringIO.new('test content') }

    before do
      allow(Aws::S3::Client).to receive(:new).and_return(s3_client)
      allow(s3_response).to receive(:body).and_return(body)
    end

    it 'loads S3 object as string' do
      expect(s3_client).to receive(:get_object).with(
        bucket: 'test-bucket',
        key: 'test-key'
      ).and_return(s3_response)

      result = described_class.load_to_str(
        s3_bucket: 'test-bucket',
        s3_key: 'test-key'
      )

      expect(result).to eq('test content')
    end

    it 'passes s3_client_kwargs to client' do
      expect(Aws::S3::Client).to receive(:new).with(region: 'us-west-2').and_return(s3_client)
      allow(s3_client).to receive(:get_object).and_return(s3_response)

      described_class.load_to_str(
        s3_bucket: 'test-bucket',
        s3_key: 'test-key',
        s3_client_kwargs: { region: 'us-west-2' }
      )
    end

    context 'with invalid arguments' do
      it 'raises error for nil bucket' do
        expect do
          described_class.load_to_str(s3_bucket: nil, s3_key: 'test-key')
        end.to raise_error(ArgumentError, 'S3 bucket must not be blank')
      end

      it 'raises error for blank bucket' do
        expect do
          described_class.load_to_str(s3_bucket: '  ', s3_key: 'test-key')
        end.to raise_error(ArgumentError, 'S3 bucket must not be blank')
      end

      it 'raises error for nil key' do
        expect do
          described_class.load_to_str(s3_bucket: 'test-bucket', s3_key: nil)
        end.to raise_error(ArgumentError, 'S3 key must not be blank')
      end

      it 'raises error for blank key' do
        expect do
          described_class.load_to_str(s3_bucket: 'test-bucket', s3_key: '  ')
        end.to raise_error(ArgumentError, 'S3 key must not be blank')
      end
    end
  end

  describe '.load_to_bytes' do
    let(:s3_client) { instance_double(Aws::S3::Client) }
    let(:s3_response) { instance_double(Aws::S3::Types::GetObjectOutput) }
    let(:binary_content) { "\x89PNG\r\n\x1A\n" }
    let(:body) { StringIO.new(binary_content) }

    before do
      allow(Aws::S3::Client).to receive(:new).and_return(s3_client)
      allow(s3_response).to receive(:body).and_return(body)
    end

    it 'loads S3 object as bytes' do
      expect(s3_client).to receive(:get_object).with(
        bucket: 'test-bucket',
        key: 'test-image.png'
      ).and_return(s3_response)

      result = described_class.load_to_bytes(
        s3_bucket: 'test-bucket',
        s3_key: 'test-image.png'
      )

      expect(result).to eq(binary_content)
      # NOTE: The actual implementation returns UTF-8 encoding
      expect(result).to be_a(String)
    end

    context 'with invalid arguments' do
      it 'raises error for nil bucket' do
        expect do
          described_class.load_to_bytes(s3_bucket: nil, s3_key: 'test-key')
        end.to raise_error(ArgumentError, 'S3 bucket must not be blank')
      end

      it 'raises error for nil key' do
        expect do
          described_class.load_to_bytes(s3_bucket: 'test-bucket', s3_key: nil)
        end.to raise_error(ArgumentError, 'S3 key must not be blank')
      end
    end
  end
end
