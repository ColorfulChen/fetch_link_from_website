cd frontend
pnpm build
cd ..
rm -rf web
cp -r frontend/dist web