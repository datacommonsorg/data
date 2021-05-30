py_binary(
    name = "parser",
    srcs = [
        "parser.py",
    ],
    data = [":data"],
    python_version = "PY3",
    deps = [
        "//file/colossus/public:cns",
        "//net/proto2/python/public:use_pure_python",  # fixdeps: keep go/proto_python_default
        "//pyglib:gfile",
        "//pyglib:resources",
        "//third_party/py/absl:app",
        "//third_party/py/rdflib_jsonld",
    ],
)

py_binary(
    name = "schema",
    srcs = ["schema.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pipeline/flume/py:runner",
        "//third_party/py/apache_beam",
    ],
)

genmpm(
    name = "encode_parser_mpm",
    temporal = 1,
    deps = [":parser_pkg"],
)

go_binary(
    name = "gen",
    srcs = ["gen.go"],
    data = ["enc_list.txt"],
    deps = [
        "//base/go:google",
        "//base/go:log",
        "//base/go:runfiles",
        "//file/base/go:file",
    ],
)

Fileset(
    name = "data",
    out = "parser_data",
    entries = [
        FilesetEntry(
            files = ["terms.json"],
        ),
    ],
)
