#
# Create docker container nnmbot 
# run script in tools dir.
# If run in other location change SRC var

SRC='../'
NAME_IMAGE='dimania/nnmbot'

# copy files for container to tmp

temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

cp ${SRC}/*.py $temp_dir
cp -R ${SRC}/locales $temp_dir
cp -R ${SRC}/tools/icu $temp_dir
cp ${SRC}/requirements.txt $temp_dir

docker build --no-cache --file ${SRC}/tools/Dockerfile -t ${NAME_IMAGE} $temp_dir

#docker push ${NAME_IMAGE}

rm -rf "$temp_dir"
