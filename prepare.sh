uv pip install -e test_proj/
uvx --from nblite@latest nbl export 
cd test_proj
uvx --from nblite@latest nbl prepare --include-dunders --fill-unchanged
cd ..
uvx --from nblite@latest nbl prepare --allow-export-during --fill-unchanged -n 2