# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require_relative 'constants'

module ImageCaptioningAssistant
  module Data
    # Generic container for values with explanations
    class ExplainedValue
      attr_accessor :value, :explanation

      def initialize(value:, explanation:)
        @value = value
        @explanation = explanation
        validate!
      end

      def validate!
        raise ArgumentError, 'Value cannot be nil' if @value.nil?
        raise ArgumentError, 'Explanation is required' if @explanation.nil? || @explanation.empty?
      end

      def to_h
        {
          value: @value,
          explanation: @explanation
        }
      end
    end

    # Container for transcribed text elements in a page
    class PageTranscription
      attr_accessor :printed_text, :handwriting

      def initialize(printed_text: [], handwriting: [])
        @printed_text = printed_text
        @handwriting = handwriting
        validate!
      end

      def validate!
        raise ArgumentError, 'printed_text must be an array' unless @printed_text.is_a?(Array)
        raise ArgumentError, 'handwriting must be an array' unless @handwriting.is_a?(Array)
      end

      def to_h
        {
          printed_text: @printed_text,
          handwriting: @handwriting
        }
      end
    end

    # Container for transcribed text elements across multiple pages
    class Transcription
      attr_accessor :transcriptions, :model_notes

      def initialize(transcriptions: [], model_notes: '')
        @transcriptions = transcriptions.map { |t| t.is_a?(PageTranscription) ? t : PageTranscription.new(**t) }
        @model_notes = model_notes
        validate!
      end

      def validate!
        raise ArgumentError, 'transcriptions must be an array' unless @transcriptions.is_a?(Array)
        raise ArgumentError, 'model_notes must be a string' unless @model_notes.is_a?(String)
      end

      def to_h
        {
          transcriptions: @transcriptions.map(&:to_h),
          model_notes: @model_notes
        }
      end
    end

    # Primary metadata container for cultural heritage materials
    class Metadata
      attr_accessor :description, :transcription, :date, :location, :publication_info,
                    :contextual_info, :format, :genre, :objects, :actions, :people, :topics

      def initialize(attributes = {})
        @description = convert_to_explained_value(attributes[:description])
        @transcription = convert_to_transcription(attributes[:transcription])
        @date = convert_to_explained_value(attributes[:date])
        @location = convert_to_explained_value(attributes[:location])
        @publication_info = convert_to_explained_value(attributes[:publication_info])
        @contextual_info = convert_to_explained_value(attributes[:contextual_info])
        @format = convert_to_explained_value(attributes[:format])
        @genre = convert_to_explained_value(attributes[:genre])
        @objects = convert_to_explained_value(attributes[:objects])
        @actions = convert_to_explained_value(attributes[:actions])
        @people = convert_to_explained_value(attributes[:people])
        @topics = convert_to_explained_value(attributes[:topics])
        validate!
      end

      def validate!
        [@description, @date, @location, @publication_info, @contextual_info,
         @format, @genre, @objects, @actions, @people, @topics].each do |field|
          raise ArgumentError, 'Required field is missing' if field.nil?
        end

        raise ArgumentError, 'Transcription is required' if @transcription.nil?

        # Validate format is a valid LibraryFormat
        return if Constants::LibraryFormat.all.include?(@format.value)

        raise ArgumentError, "Invalid format value: #{@format.value}"
      end

      def to_h
        {
          description: @description.to_h,
          transcription: @transcription.to_h,
          date: @date.to_h,
          location: @location.to_h,
          publication_info: @publication_info.to_h,
          contextual_info: @contextual_info.to_h,
          format: @format.to_h,
          genre: @genre.to_h,
          objects: @objects.to_h,
          actions: @actions.to_h,
          people: @people.to_h,
          topics: @topics.to_h
        }
      end

      private

      def convert_to_explained_value(value)
        return value if value.is_a?(ExplainedValue)
        return ExplainedValue.new(**value) if value.is_a?(Hash)

        nil
      end

      def convert_to_transcription(value)
        return value if value.is_a?(Transcription)
        return Transcription.new(**value) if value.is_a?(Hash)

        nil
      end
    end

    # Individual bias assessment
    class Bias
      attr_accessor :level, :type, :explanation

      def initialize(level: nil, type: nil, explanation: nil)
        # Handle string keys from JSON
        @level = level || (respond_to?(:[]) ? self['level'] : nil)
        @type = type || (respond_to?(:[]) ? self['type'] : nil)
        @explanation = explanation || (respond_to?(:[]) ? self['explanation'] : nil)
        validate!
      end

      def validate!
        raise ArgumentError, 'Invalid bias level' unless Constants::BiasLevel.all.include?(@level)
        raise ArgumentError, 'Invalid bias type' unless Constants::BiasType.all.include?(@type)
        raise ArgumentError, 'Explanation is required' if @explanation.nil? || @explanation.empty?
      end

      def to_h
        {
          level: @level,
          type: @type,
          explanation: @explanation
        }
      end
    end

    # Collection of biases
    class Biases
      attr_accessor :biases

      def initialize(biases: [])
        # Handle both array of hashes and array of Bias objects
        @biases = biases.map do |b|
          if b.is_a?(Bias)
            b
          else
            # Convert hash with string keys to Bias object
            Bias.new(
              level: b['level'],
              type: b['type'],
              explanation: b['explanation']
            )
          end
        end
        validate!
      end

      def validate!
        raise ArgumentError, 'biases must be an array' unless @biases.is_a?(Array)

        @biases.each(&:validate!)
      end

      def to_h
        {
          biases: @biases.map(&:to_h)
        }
      end
    end

    # Complete bias analysis for a work
    class WorkBiasAnalysis
      attr_accessor :metadata_biases, :page_biases

      def initialize(metadata_biases: nil, page_biases: nil, **_kwargs)
        # Handle direct initialization with hash values
        @metadata_biases = if metadata_biases.is_a?(Hash)
                             Biases.new(biases: metadata_biases['biases'] || [])
                           else
                             metadata_biases || Biases.new
                           end

        # Handle page_biases as array of hashes or array of Biases objects
        @page_biases = if page_biases.is_a?(Array)
                         page_biases.map do |pb|
                           if pb.is_a?(Hash)
                             Biases.new(biases: pb['biases'] || [])
                           else
                             pb
                           end
                         end
                       else
                         []
                       end

        validate!
      end

      def validate!
        raise ArgumentError, 'metadata_biases must be a Biases object' unless @metadata_biases.is_a?(Biases)
        raise ArgumentError, 'page_biases must be an array' unless @page_biases.is_a?(Array)

        @page_biases.each { |pb| raise ArgumentError, 'Invalid page bias' unless pb.is_a?(Biases) }
      end

      def to_h
        {
          metadata_biases: @metadata_biases.to_h,
          page_biases: @page_biases.map(&:to_h)
        }
      end
    end

    # Custom error for document length issues
    class DocumentLengthError < StandardError
      attr_reader :error_code

      def initialize(message, error_code = nil)
        @error_code = error_code
        super(message)
      end
    end
  end
end
