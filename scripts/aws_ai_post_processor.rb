# frozen_string_literal: true
require 'csv'

class AwsAiPostProcessor
  HEADER_FIELDS = [
    'deduplication_key', 'subject_geo', 'description', 'place_of_production', 'publisher', 'subject_topics', 'content_genres', 'date_created',
    'abstract', 'content_type', 'other_identifiers', 'administrative_unit', 'local_call_number', 'creator', 'holding_repository',
    'institution', 'primary_language', 'notes', 'emory_rights_statements', 'rights_statement', 'subject_names', 'title', 'data_classifications',
    'Ingest.workflow_notes', 'visibility', 'Directory Path', 'File Size', 'Filename', 'Path', 'Ingest.workflow_rights_basis',
    'Ingest.workflow_rights_basis_date', 'Ingest.workflow_rights_basis_note', 'copyright_date', 'rights_holders', 'Accession.workflow_rights_basis',
    'Accession.workflow_rights_basis_reviewer', 'Accession.workflow_rights_basis_note', 'sensitive_material', 'sensitive_material_note', 'extent',
    'sublocation'
  ]
  MATCHERS = {
    'deduplication_key': ['work_id'],
    'subject_geo': ['location'],
    'description': ['transcription'],
    'place_of_production': ['publication_info'],
    'publisher': ['publication_info'],
    'subject_topics': ['objects', 'topics', 'people'],
    'content_genres': ['genre'],
    'date_created': ['date'],
    'abstract': ['description'],
    'content_type': ['format']
  }

  def initialize(csv)
    @csv = csv
    @ret_arr = []
  end

  def process
    process_csv_lines
    process_objects
    process_return_csv
  end

  private

  def process_csv_lines
    csv_file = File.open(@csv)
    @ai_objs = CSV.parse(csv_file.read, headers: true)
  end

  def process_objects
    processed_objects = @ai_objs.select { |obj| obj['work_status'] == 'READY FOR REVIEW' }

    processed_objects.each do |obj|
      elem_arr = []
      matcher_fields = MATCHERS.keys.map(&:to_s)

      HEADER_FIELDS.each do |field|
        elem_arr.push(matcher_fields.include?(field) ? MATCHERS[field.to_sym].map { |ai_field| obj[ai_field]}.compact.join('|') : '')
      end
      @ret_arr << elem_arr
    end
  end

  def process_return_csv
    CSV.open("ai_post_processed_ingest_#{DateTime.now.strftime('%Y%m%dT%H%M')}.csv", "wb") do |csv|
      csv << HEADER_FIELDS
      @ret_arr.each { |arr| csv << arr }
    end
  end
end
