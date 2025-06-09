uv pip install test_proj/
uvx --from nblite nbl export 
cd test_proj
nbl prepare --include-underscores
cd ..
nbl prepare --allow-export-during --fill-unchanged -n 2