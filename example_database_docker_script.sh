#!bin/sh
# docker run --name mongo6-jammy -p 27017:27017 \
#     -e MONGO_INITDB_ROOT_USERNAME=admin \
#     -e MONGO_INITDB_ROOT_PASSWORD=VRuAd2Nvmp4ELHh5 \
#     -e MONGO_INITDB_DATABASE=test \
#     -v /root/fetch_link_from_website/database/data:/data/db \
#     mongo:6-jammy

docker run -d --name mongo6-jammy -p 27017:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=admin \
    -e MONGO_INITDB_ROOT_PASSWORD=VRuAd2Nvmp4ELHh5 \
    -e MONGO_INITDB_DATABASE=test \
    -v /root/fetch_link_from_website/database/data:/data/db \
    --restart=unless-stopped \
    mongo:6-jammy
