# frozen_string_literal: true
require 'faraday'
require 'csv'

class AwsAiCsvProcessor
  FIELDS_TO_PULL = [
    ['title', 'title_tesim'],
    ['abstract', 'abstract_tesim'],
    ['administrative_unit', 'administrative_unit_tesim'],
    ['contact_information', 'contact_information_tesim'],
    ['content_genres', 'content_genres_tesim'],
    ['content_type', 'content_type_tesim'],
    ['date_created', 'human_readable_date_created_tesim'],
    ['deduplication_key', 'deduplication_key_tesim'],
    ['emory_rights_statements', 'emory_rights_statements_tesim'],
    ['extent', 'extent_tesim'],
    ['holding_repository', 'holding_repository_tesim'],
    ['institution', 'institution_tesim'],
    ['legacy_rights', 'legacy_rights_tesim'],
    ['local_call_number', 'local_call_number_tesim'],
    ['notes', 'notes_tesim'],
    ['other_identifiers', 'other_identifiers_tesim'],
    ['rights_statement', 'rights_statement_tesim'],
    ['subject_geo', 'subject_geo_tesim'],
    ['subject_names', 'subject_names_tesim'],
    ['subject_topics', 'subject_topics_tesim'],
    ['sublocation', 'sublocation_tesim']
  ]

  def initialize(csv)
    @csv = csv
    @ret_arr = []
    @solr_path = 'http://solr-cor.library.emory.edu/solr/curate_collection/select?'
  end

  def process
    process_csv_lines
    process_file_objs
    process_return_csv
  end

  def process_all_pages_in_works
    process_csv_lines
    process_all_files_in_works
    process_return_csv
  end

  private

  def process_csv_lines
    csv_file = File.open(@csv)
    @file_objs = CSV.parse(csv_file.read, headers: true)
  end

  def process_file_objs
    @file_objs.each { |obj| process_file(obj) }
  end

  def process_all_files_in_works
    @file_objs.each { |obj| process_work(obj) }
  end

  def process_file(obj)
    ret_obj = beginning_hsh(obj)
    work_query = Faraday.new(url: work_query_path(obj['work_id'])).get
    work = JSON.parse(work_query.body)['response']['docs'].first
    file_set_query = Faraday.new(url: file_set_query_path(obj['file_set_id'])).get
    file_set = JSON.parse(file_set_query.body)['response']['docs'].first
    pull_work_metadata(work, ret_obj)
    pull_file_set_data(file_set, ret_obj)
    @ret_arr << ret_obj
  end

  def process_work(obj)
    work_query = Faraday.new(url: work_only_query_path(obj['work_id'])).get
    work = JSON.parse(work_query.body)['response']['docs'].first
    filesets = work['member_ids_ssim'].map do |id|
      file_set_query = Faraday.new(url: work_only_file_set_query_path(id)).get
      JSON.parse(file_set_query.body)['response']['docs'].first
    end

    filesets.each do |fs|
      if fs['has_model_ssim'].include?('FileSet') && fs['title_tesim'].first.include?('Page') && !fs['sha1_tesim'].nil?
        ret_obj = beginning_hsh(obj)

        pull_work_metadata(work, ret_obj)
        pull_file_set_data(fs, ret_obj)
        ret_obj['file_set_id'] = fs['id']
        @ret_arr << ret_obj
      end
    end
  end

  def pull_work_metadata(work, ret_obj)
    FIELDS_TO_PULL.each { |field_name, field_solr| ret_obj[field_name] = work[field_solr] }
  end

  def pull_file_set_data(file_set, ret_obj)
    ret_obj['page_sha1'] = if file_set['title_tesim'].include?('Front') || file_set['title_tesim'].include?('Back')
                             file_set['sha1_tesim'][1].partition("urn:sha1:").last
                           else
                             file_set['sha1_tesim'].first.partition("urn:sha1:").last
                           end
    ret_obj['page_title'] = file_set['title_tesim']
  end

  def process_return_csv
    CSV.open("aws_ai_#{DateTime.now.strftime('%Y%m%dT%H%M')}.csv", "wb") do |csv|
      csv << @ret_arr.first.keys
      @ret_arr.each do |elem|
        converted_val_arr = elem.values.map { |v| v.is_a?(Array) ? v.join('|') : v }
        csv << converted_val_arr
      end
    end
  end

  def work_query_path(work_id)
    @solr_path + "fl=" + FIELDS_TO_PULL.map { |f| f[1] }.join('%2C%20') + "&q=id:" + work_id + "&wt=json"
  end

  def work_only_query_path(work_id)
    @solr_path + "fl=" + FIELDS_TO_PULL.map { |f| f[1] }.push('member_ids_ssim').join('%2C%20') + "&q=id:" + work_id + "&wt=json"
  end

  def file_set_query_path(file_set_id)
    @solr_path + "fl=title_tesim%2C%20sha1_tesim&q=id:" + file_set_id + "&wt=json"
  end

  def work_only_file_set_query_path(file_set_id)
    @solr_path + "fl=title_tesim%2C%20sha1_tesim%2C%20has_model_ssim%2C%20id&q=id:" + file_set_id + "&wt=json"
  end

  def beginning_hsh(obj)
    { 'work_id': obj['work_id'],
      'file_set_id': obj['file_set_id'],
      'work_link': obj['work_link'],
      'file_set_link': obj['file_set_link'],
      'collection_link': obj['collection_link'],
      'notes_from_elizabeth': obj['notes_from_elizabeth'],
      'page_context_from_elizabeth': obj['page_context_from_elizabeth'],
      'category_from_elizabeth': obj['category_from_elizabeth'] }
  end
end
