uv pip install -e test_proj/
uvx --from . nbl export 
cd test_proj
uvx --from . nbl prepare --include-dunders --fill-unchanged
cd ..
uvx --from . nbl prepare --allow-export-during --fill-unchanged -n 2