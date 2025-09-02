from setuptools import Extension, setup

setup(
    name="customext",
    version="0.1.0",
    ext_modules=[
        Extension(
            "customext",
            sources=["customext.c"],
        )
    ],
)
