import {
    Alert,
    Box,
    Card,
    CardContent,
    CircularProgress,
    Grid,
    Typography,
} from "@mui/material";

import { useDashboard } from "../hooks/useDashboard";

export function DashboardPage() {

    const { stats, loading, error } = useDashboard();

    if (loading) {

        return (

            <Box
                display="flex"
                justifyContent="center"
                alignItems="center"
                height="70vh"
            >
                <CircularProgress />

            </Box>

        );

    }

    if (error) {

        return <Alert severity="error">{error}</Alert>;

    }

    const cards = [

        {

            title: "Clientes",

            value: stats?.customers,

        },

        {

            title: "Conversaciones",

            value: stats?.conversations,

        },

        {

            title: "Preaprobados",

            value: stats?.preapproved,

        },

        {

            title: "Observados",

            value: stats?.observed,

        },

    ];

    return (

        <Box>

            <Typography variant="h4" fontWeight="bold" mb={4}>

                Dashboard

            </Typography>

            <Grid container spacing={3}>

                {cards.map((card) => (

                    <Grid item xs={12} md={3} key={card.title}>

                        <Card>

                            <CardContent>

                                <Typography color="text.secondary">

                                    {card.title}

                                </Typography>

                                <Typography variant="h3">

                                    {card.value}

                                </Typography>

                            </CardContent>

                        </Card>

                    </Grid>

                ))}

            </Grid>

        </Box>

    );

}