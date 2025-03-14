# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

module ImageCaptioningAssistant
  module Data
    module Constants
      # Different levels of bias
      module BiasLevel
        LOW = "low"           # Low potential for harm: unintentional exclusion
        MEDIUM = "medium"     # Medium potential for harm: obsolete language terms
        HIGH = "high"         # High potential for harm: offensive terminology

        def self.all
          [LOW, MEDIUM, HIGH]
        end
      end

      # Different types of bias
      module BiasType
        GENDER = "gender"
        RACIAL = "racial"
        SEXUAL = "sexual"
        CULTURAL = "cultural"
        ABILITY = "ability"
        SEXUAL_ORIENTATION = "sexual orientation"
        BODY_SHAPE = "body shape"
        AGE = "age"
        VIOLENCE = "violence"
        POLITICAL = "political"
        NUDITY = "nudity"
        OTHER = "other"

        def self.all
          constants.map { |c| const_get(c) }
        end
      end

      # Allowed format values for library materials
      module LibraryFormat
        ARTIFACT = "Artifact"
        AUDIO = "Audio"
        CARTOGRAPHIC = "Cartographic"
        COLLECTION = "Collection"
        DATASET = "Dataset"
        DIGITAL = "Digital"
        MANUSCRIPT = "Manuscript"
        MIXED_MATERIAL = "Mixed Material"
        MOVING_IMAGE = "Moving Image"
        MULTIMEDIA = "Multimedia"
        NOTATED_MUSIC = "Notated Music"
        STILL_IMAGE = "Still Image"
        TACTILE = "Tactile"
        TEXT = "Text"
        UNSPECIFIED = "Unspecified"

        def self.all
          constants.map { |c| const_get(c) }
        end
      end
    end
  end
end
