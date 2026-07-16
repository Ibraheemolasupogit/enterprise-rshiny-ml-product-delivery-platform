# 0026 Raw Input API Contract With Registered Preprocessor

Status: Accepted

Context: API callers should not submit transformed one-hot feature vectors.

Decision: The API accepts raw admission-time predictors and applies the registered preprocessing contract.

Consequences: Feature order and preprocessor fingerprints are validated before prediction.

Alternatives considered: Requiring callers to submit 71 transformed fields was rejected as brittle and unsafe.
