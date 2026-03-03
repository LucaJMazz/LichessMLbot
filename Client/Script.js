if (process.argv[2]  == 0) {
    var BASE_URL = 'https://lichessmlbot.onrender.com'
} else {
    var BASE_URL = 'http://localhosst:3000'
}

var moves = [];

setInterval(async ()=> {
    const res = await fetch(`${BASE_URL}/moves`)
    const data = await res.json()
    
    if (data !== null) {
        if (data.join(' ') !== moves.join(' ')) {
            console.log('New moves:', data)
            moves = data;

        }
    }
}, 500)


async function sendMove(move) {
    if (move != null) {
        console.log("Arg:", move);

        const res = await fetch(`${BASE_URL}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                move: move,
            })
        });

        const data = await res.json();
        console.log(data);
    }
}

sendMove(process.argv[3]);