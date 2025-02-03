# Metadata CRUD operations
def create_metadata(
    db: Session,
    job_id: int,
    document_id: int,
    description: str,
    transcription: str,
    people_and_groups: str,
    date: datetime,
    location: str,
    publication_info: str,
    contextual_info: str,
    bias_id: int,
):
    new_metadata = Metadata(
        job_id=job_id,
        document_id=document_id,
        description=description,
        transcription=transcription,
        people_and_groups=people_and_groups,
        date=date,
        location=location,
        publication_info=publication_info,
        contextual_info=contextual_info,
        bias_id=bias_id,
    )
    db.add(new_metadata)
    db.commit()
    db.refresh(new_metadata)
    return new_metadata


def read_metadata(db: Session, metadata_id: int):
    return db.query(Metadata).filter(Metadata.metadata_id == metadata_id).first()


def update_metadata(db: Session, metadata_id: int, **kwargs):
    db.execute(
        update(Metadata).where(Metadata.metadata_id == metadata_id).values(**kwargs)
    )
    db.commit()
    return read_metadata(db, metadata_id)


def delete_metadata(db: Session, metadata_id: int):
    db.execute(delete(Metadata).where(Metadata.metadata_id == metadata_id))
    db.commit()


# Document Bias CRUD operations
def create_document_bias(
    db: Session,
    job_id: int,
    document_id: str,
    bias_type: str,
    bias_level: str,
    explanation: str,
):
    new_doc_bias = DocumentBias(
        job_id=job_id,
        document_id=document_id,
        bias_type=bias_type,
        bias_level=bias_level,
        explanation=explanation,
    )
    db.add(new_doc_bias)
    db.commit()
    db.refresh(new_doc_bias)
    return new_doc_bias


def read_document_bias(db: Session, bias_id: int):
    return db.query(DocumentBias).filter(DocumentBias.bias_id == bias_id).first()


def update_document_bias(db: Session, bias_id: int, **kwargs):
    db.execute(
        update(DocumentBias).where(DocumentBias.bias_id == bias_id).values(**kwargs)
    )
    db.commit()
    return read_document_bias(db, bias_id)


def delete_document_bias(db: Session, bias_id: int):
    db.execute(delete(DocumentBias).where(DocumentBias.bias_id == bias_id))
    db.commit()
