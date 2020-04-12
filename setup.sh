#! bin/bash

ps1="pc444"
ps2="pc501"

pc="pc508 pc460 pc447 pc443 pc506 pc484 pc499 pc490"

Script="curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py;
		python3 get-pip.py --force-reinstall;

		git clone https://github.com/BharathGottumukkala/pBFT.git;
		cd pBFT;
		/users/ConMan/.local/bin/pip3 install -r requirements1.txt;"

# Run index.py in the first node
ssh -o StrictHostKeyChecking=no -p 22 ConMan@${pc1}.emulab.net "${Script} python3 index.py"

# Run Namescheduler.py in the next node
ssh -o StrictHostKeyChecking=no -p 22 ConMan@${pc2}.emulab.net "${Script} python3 NameScheduler.py"


# Run Node.py in the rest of the nodes
for pcname in ${pc} ; do
    ssh -o StrictHostKeyChecking=no -p 22 ConMan@${pc2}.emulab.net "${Script} python3 Node.py"
done

