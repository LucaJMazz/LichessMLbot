import express from 'express'
import cors from 'cors'
import { getMoves, getGame, postMove } from './LichessStream.js'

const app = express()
const PORT = process.env.PORT || 3000;

app.use(cors())
app.use(express.json())

app.get('/moves', (req, res) => {
    const moves = getMoves();
    res.json(moves)
})

app.post('/move', (req, res) => {
    const { move } = req.body;
    if (!move) {
        return res.status(400).json({ error: "Move is required" });
    }
    console.log("Move received:", move);
    postMove(move);
    return res.status(200).json({ success:true })
})

app.get('/getGame', (req, res) => {
    const game = getGame();
    res.json(game)
})

app.listen(PORT, () => {
    console.log(`Server running on ${PORT}`)
})