while ! ping -w 20 -c 1 `ip r | grep default | cut -d ' ' -f 3` &> /dev/null
do
  printf "attempting to find gateway"
done

#the area in backticks grabs the default gateway for network interface
