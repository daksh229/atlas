"""Build everything in one shot: base tables + Atlas cross-match + RAG corpus."""

import init_db
import init_atlas
import generate_corpus

if __name__ == "__main__":
    init_db.main()
    init_atlas.main()
    generate_corpus.main()
