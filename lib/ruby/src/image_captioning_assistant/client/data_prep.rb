# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'aws-sdk-s3'
require 'json'
require 'logger'
require 'tempfile'
require 'mini_magick'
require 'open3'
require 'csv'
require 'parallel'
require 'fileutils'
require 'stringio'

# Data prep utils for the api_gateway_demo notebook
class DataPrepUtils
  def self.populate_bucket(bucket_name, image_fpath, context, metadata, convert_jpeg = true)
    # Initialize S3 client
    s3_client = Aws::S3::Client.new

    # Get image filename and create key
    image_filename = File.basename(image_fpath)
    base_name = File.basename(image_filename, File.extname(image_filename))

    if convert_jpeg
      # Convert the image to JPEG
      begin
        img = MiniMagick::Image.open(image_fpath)
        img.colorspace('RGB') if img.colorspace != 'RGB'

        # Save to a temporary file
        temp_file = Tempfile.new(['temp', '.jpg'])
        temp_path = temp_file.path
        img.format('jpg')
        img.quality(95)
        img.write(temp_path)

        # Use the temporary file for upload
        image_key = "images/#{base_name}.jpg"
        s3_client.put_object(
          body: File.open(temp_path, 'rb'),
          bucket: bucket_name,
          key: image_key,
          content_type: 'image/jpeg'
        )

        # Clean up
        temp_file.close
        temp_file.unlink
      rescue StandardError => e
        logger = Logger.new(STDOUT)
        logger.error("Failed to convert image: #{e.message}. Uploading original.")
        image_key = "images/#{image_filename}"
        s3_client.put_object(
          body: File.open(image_fpath, 'rb'),
          bucket: bucket_name,
          key: image_key
        )
      end
    else
      # Upload original image file
      image_key = "images/#{image_filename}"
      s3_client.put_object(
        body: File.open(image_fpath, 'rb'),
        bucket: bucket_name,
        key: image_key
      )
    end

    # Create image S3 URI
    image_s3_uri = "s3://#{bucket_name}/#{image_key}"

    # Upload metadata JSON file
    original_metadata_key = "metadata/#{base_name}_metadata.txt"
    s3_client.put_object(
      body: metadata,
      bucket: bucket_name,
      key: original_metadata_key
    )
    # Create metadata S3 URI
    original_metadata_s3_uri = "s3://#{bucket_name}/#{original_metadata_key}"

    # Upload context JSON file
    context_key = "contexts/#{base_name}_context.txt"
    s3_client.put_object(
      body: context,
      bucket: bucket_name,
      key: context_key
    )
    # Create context S3 URI
    context_s3_uri = "s3://#{bucket_name}/#{context_key}"

    [image_s3_uri, original_metadata_s3_uri, context_s3_uri]
  end

  def self.convert_to_jpeg(file_content)
    # Create temporary file to handle binary data
    temp_file = Tempfile.new(['temp', '.bin'])
    temp_file.binmode
    temp_file.write(file_content)
    temp_file.close

    # Open the image with MiniMagick
    img = MiniMagick::Image.open(temp_file.path)

    # Convert to RGB if needed
    img.colorspace('RGB') if img.colorspace != 'RGB'

    # Save as JPEG to a new tempfile
    output_file = Tempfile.new(['output', '.jpg'])
    output_path = output_file.path
    img.format('jpg')
    img.quality(95)
    img.write(output_path)

    # Get the bytes
    jpeg_content = File.binread(output_path)

    # Clean up
    temp_file.unlink
    output_file.close
    output_file.unlink

    jpeg_content
  rescue StandardError => e
    logger = Logger.new(STDOUT)
    logger.error("Failed to convert image to JPEG: #{e.message}")
    # Return original content if conversion fails
    file_content
  end

  def self.copy_s3_file_using_subprocess(source_bucket, source_key, dest_bucket, dest_key, convert_jpeg = true)
    logger = Logger.new(STDOUT)
    logger.debug("Trying alternative method with AWS CLI for #{source_key}")

    if convert_jpeg
      temp_file = Tempfile.new(['temp', '.jpg'])
      temp_path = temp_file.path

      # Download the file
      download_cmd = "aws s3 cp s3://#{source_bucket}/#{source_key} #{temp_path}"
      system(download_cmd)

      # Convert to JPEG
      begin
        img = MiniMagick::Image.open(temp_path)
        img.colorspace('RGB') if img.colorspace != 'RGB'
        img.format('jpg')
        img.quality(95)
        img.write(temp_path)
      rescue StandardError => e
        logger.error("Failed to convert image using subprocess method: #{e.message}")
      end

      # Upload the converted file
      upload_cmd = "aws s3 cp #{temp_path} s3://#{dest_bucket}/#{dest_key}"
      _, stderr, status = Open3.capture3(upload_cmd)

      # Clean up
      temp_file.close
      temp_file.unlink
    else
      cmd = "aws s3 cp s3://#{source_bucket}/#{source_key} s3://#{dest_bucket}/#{dest_key}"
      _, stderr, status = Open3.capture3(cmd)
    end

    if status.success?
      logger.debug("Successfully copied #{source_key} using AWS CLI")
    else
      logger.error("AWS CLI copy failed: #{stderr}")
    end
  end

  def self.copy_s3_file(source_bucket, source_key, dest_bucket, dest_key, convert_jpeg = true)
    logger = Logger.new(STDOUT)
    s3_client = Aws::S3::Client.new

    begin
      logger.debug("Copying #{source_bucket}/#{source_key} to #{dest_bucket}/#{dest_key}")
      response = s3_client.get_object(bucket: source_bucket, key: source_key)
      file_content = response.body.read

      # Convert to JPEG if requested
      file_content = convert_to_jpeg(file_content) if convert_jpeg

      s3_client.put_object(
        body: file_content,
        bucket: dest_bucket,
        key: dest_key,
        content_type: 'image/jpeg'
      )
    rescue StandardError => e
      logger.error("Error: #{e.message}")
      copy_s3_file_using_subprocess(
        source_bucket,
        source_key,
        dest_bucket,
        dest_key,
        convert_jpeg
      )
    end
  end

  def self.convert_page_to_index(page_string)
    # Handle "Front" case
    if page_string == 'Front'
      return 0
    # Handle "Back" case
    elsif page_string == 'Back'
      return 1 # Or another appropriate value
    # Handle "Page X" case
    elsif page_string.start_with?('Page ')
      # Extract the number after "Page "
      match = page_string.match(/Page (\d+)/)
      return match[1].to_i if match
    end

    raise 'Page was not formatted as expected'
  end

  def self.prepare_images(work_df, job_name, uploads_bucket, original_bucket)
    # Get work ID
    work_id = work_df.first['work_id']
    # Create the destination path
    destination_folder = "#{job_name}/#{work_id}/images/"
    # Loop through each row in the dataframe

    work_df.each do |row|
      # Get the original file path/key and other necessary info
      page_sha = row['page_sha1']
      page_index = convert_page_to_index(row['page_title'])
      # Copy the file with the new naming convention and convert to JPEG
      copy_s3_file(
        source_bucket: original_bucket,
        source_key: page_sha,
        dest_bucket: uploads_bucket,
        dest_key: "#{destination_folder}page_#{page_index.to_s.rjust(5, '0')}_#{page_sha}.jpg",
        convert_jpeg: true
      )
    end

    # Return the destination folder URI in S3 format
    ["s3://#{uploads_bucket}/#{destination_folder}"]
  end

  def self.prepare_metadata(work_df, job_name, uploads_bucket)
    # Create metadata dictionary
    metadata = {
      'title' => work_df.first['title'],
      'abstract' => work_df.first['abstract']
    }
    # Define the metadata S3 URI
    work_id = work_df.first['work_id']
    metadata_s3_key = "#{job_name}/#{work_id}/metadata.json"
    # Write metadata to S3
    s3 = Aws::S3::Client.new
    s3.put_object(
      bucket: uploads_bucket,
      key: metadata_s3_key,
      body: JSON.dump(metadata),
      content_type: 'application/json'
    )
    # Create the URI
    "s3://#{uploads_bucket}/#{metadata_s3_key}"
  end

  def self.process_single_work_group(work_id, work_df, job_name, uploads_bucket, original_bucket)
    # Process a single work group to create a job object
    images_s3_uris = prepare_images_parallel(
      work_df: work_df,
      job_name: job_name,
      uploads_bucket: uploads_bucket,
      original_bucket: original_bucket
    )
    metadata_s3_uri = prepare_metadata(
      work_df: work_df,
      job_name: job_name,
      uploads_bucket: uploads_bucket
    )

    {
      'work_id' => work_id,
      'image_s3_uris' => images_s3_uris,
      'original_metadata_s3_uri' => metadata_s3_uri
    }
  end

  def self.prepare_images_parallel(work_df:, job_name:, uploads_bucket:, original_bucket:, max_workers: 5)
    work_id = work_df.first['work_id']
    destination_folder = "#{job_name}/#{work_id}/images/"

    # Create a list of tasks (rows to process)
    tasks = []
    work_df.each do |row|
      page_sha = row['page_sha1']
      page_index = convert_page_to_index(row['page_title'])
      dest_key = "#{destination_folder}page_#{page_index.to_s.rjust(5, '0')}_#{page_sha}.jpg"
      tasks << [original_bucket, page_sha, uploads_bucket, dest_key]
    end

    # Process images in parallel
    Parallel.each(tasks, in_threads: max_workers) do |args|
      copy_s3_file(*args, true)
    end

    ["s3://#{uploads_bucket}/#{destination_folder}"]
  end

  def self.translate_csv_to_job_objects(csv_path:, job_name:, uploads_bucket:, original_bucket: 'fedora-cor-binaries', max_workers: 10)
    # Load data
    csv_data = CSV.read(csv_path, headers: true)

    # Group by work_id
    grouped = {}
    csv_data.each do |row|
      work_id = row['work_id']
      grouped[work_id] ||= []
      grouped[work_id] << row.to_h
    end

    # Process each work_id group in parallel
    Parallel.map(grouped.to_a, in_threads: max_workers) do |work_id, group_df|
      process_single_work_group(work_id, group_df, job_name, uploads_bucket, original_bucket)
    end
  end
end
