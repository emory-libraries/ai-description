# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'logger'

module ImageCaptioningAssistant
  module Generate
    module BiasAnalysis
      LOGGER = Logger.new($stdout)
      LOGGER.level = Logger::INFO

      def self.load_and_resize_image(
        image_s3_uri:,
        s3_kwargs:,
        resize_kwargs:
      )
        bucket, key = AWS::S3.parse_s3_uri(image_s3_uri)
        img_bytes = AWS::S3.load_to_bytes(
          s3_bucket: bucket,
          s3_key: key,
          s3_client_kwargs: s3_kwargs
        )

        resized_image = Utils.convert_and_reduce_image(
          image_bytes: img_bytes,
          max_dimension: resize_kwargs[:max_dimension] || 2048,
          jpeg_quality: resize_kwargs[:jpeg_quality] || 95
        )

        resized_image
      end

      def self.load_and_resize_images(
        image_s3_uris:,
        s3_kwargs:,
        resize_kwargs:
      )
        resized_img_bytes_list = []

        image_s3_uris.each do |image_s3_uri|
          resized_img_bytes = load_and_resize_image(
            image_s3_uri: image_s3_uri,
            s3_kwargs: s3_kwargs,
            resize_kwargs: resize_kwargs
          )
          resized_img_bytes_list << resized_img_bytes
        end

        resized_img_bytes_list
      end
    end
  end
end
