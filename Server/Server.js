import express from 'express'
import cors from 'cors'
import { gameEvents, postMove, getColor, getFen, getMoves, getStatus, getTurn } from './LichessStream.js'


const app = express()
const PORT = process.env.PORT || 3000;
const API_POST_KEY = process.env.API_POST_KEY;

app.use(cors())
app.use(express.json())

app.get('/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')

    const onMove = (data) => res.write(`data: ${JSON.stringify(data)}\n\n`)
    gameEvents.on('move', onMove)
    req.on('close', () => gameEvents.off('move', onMove))
});

app.get('/state', (req, res) => {
    res.json({
        fen: getFen(),  
        turn: getTurn(),
        moves: getMoves(),
        color: getColor(),
        status: getStatus()  
    })
})

app.post('/move', async (req, res) => {
    const { move } = req.body; // gets move from body of post
    const apiKey = req.headers["x-post-key"] // gets apiKey from header of post

    if (!apiKey || apiKey !== API_POST_KEY) { // Authenticates post request
        return res.status(403).json({ error: "Authorization required: Invalid API Key" });
    }

    console.log("Authorized Move received:", move);
    const result = await postMove(move);

    if (!result) {
        return res.status(500).json({ ok: false, error: "postMove returned undefined" });
    }
    if (result.ok) {
        return res.status(200).json(result);
    } else {
        return res.status(400).json(result);
    }
});


app.get('/getGame', (req, res) => {
    const game = getGame();
    res.json(game)
})

app.listen(PORT, () => {
    console.log(`Server running on ${PORT}`)
})