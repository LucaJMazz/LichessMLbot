import express from 'express'
import cors from 'cors'
import { getMoves, getGame, postMove } from './LichessStream.js'

const app = express()
const PORT = 3000;

app.use(cors())
app.use(express.static('../Client'))
app.use(express.json())

app.get('/moves', (req, res) => {
    const moves = getMoves();
    res.json(moves)
})

app.post('/move', (req, res) => {
    const { move } = req.body;
    console.log("moved");
    postMove(move);
    if (!move) {
        return res.status(400)
    }
})

app.get('/getGame', (req, res) => {
    const game = getGame();
    res.json(game)
})

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`)
})